import base64
import json
from typing import Any
from urllib.parse import quote

from erpnext_agent.api.api_client_base import ApiClientBase
from erpnext_agent.lifecycle import (
    DocumentEvent,
    DocumentState,
    Guards,
    state_of,
    transition,
)

_AMEND_DROP = {"name", "docstatus", "modified", "creation", "amended_from"}
_AMEND_ROW_DROP = {
    "name",
    "docstatus",
    "modified",
    "creation",
    "parent",
    "parenttype",
    "parentfield",
    "owner",
    "modified_by",
}


def _doc_path(doctype: str, name: str | None = None) -> str:
    """``/api/resource/<doctype>[/<name>]`` with each segment percent-encoded."""
    path = f"/api/resource/{quote(doctype, safe='')}"
    return path if name is None else f"{path}/{quote(str(name), safe='')}"


class Api(ApiClientBase):
    def login(self, usr: str | None = None, pwd: str | None = None) -> dict:
        """Authenticate yourself."""
        data = {}
        if usr:
            data["usr"] = usr
        if pwd:
            data["pwd"] = pwd
        return self.request("POST", "/api/method/login", data=data)

    def logout(self) -> dict:
        """Logout from current session."""
        return self.request("GET", "/api/method/logout")

    def get_logged_user(self) -> dict:
        """Get the user that is logged in."""
        return self.request("GET", "/api/method/frappe.auth.get_logged_user")

    def get_version(self) -> dict:
        """Get installed app versions.

        Frappe has no ``/api/method/version`` command — calling it returns a
        417 ValidationError ("Failed to get method for command version"). The
        canonical whitelisted endpoint is
        ``frappe.utils.change_log.get_versions`` (requires an authenticated
        session/token).
        """
        return self.request("GET", "/api/method/frappe.utils.change_log.get_versions")

    def get_document(self, doctype: str, name: str) -> dict:
        """Get a document resource by name."""
        return self.request("GET", _doc_path(doctype, name))

    def create_document(self, doctype: str, data: dict) -> dict:
        """Create a new document resource."""
        return self.request("POST", _doc_path(doctype), data=data)

    def update_document(self, doctype: str, name: str, data: dict) -> dict:
        """Update a specific document resource."""
        return self.request("PUT", _doc_path(doctype, name), data=data)

    def delete_document(self, doctype: str, name: str) -> dict:
        """Delete a specific document resource."""
        return self.request("DELETE", _doc_path(doctype, name))

    def list_documents(
        self,
        doctype: str,
        filters: list | dict | None = None,
        fields: list | None = None,
        limit_page_length: int = 20,
        limit_start: int = 0,
        limit: int | None = None,
    ) -> list:
        """List document resources with pagination, filters, and selected fields."""
        page_length = limit if limit is not None else limit_page_length
        params: dict[str, Any] = {
            "limit_page_length": page_length,
            "limit_start": limit_start,
        }
        if filters:
            if isinstance(filters, list | dict | tuple):
                params["filters"] = json.dumps(filters)
            else:
                params["filters"] = str(filters)
        if fields:
            if isinstance(fields, list | dict | tuple):
                params["fields"] = json.dumps(fields)
            else:
                params["fields"] = str(fields)
        return self.request("GET", _doc_path(doctype), params=params)

    def call_method(self, method: str, params: dict | None = None) -> dict:
        """Execute dotted path whitelisted RPC methods (covers 100% of custom functions)."""
        return self.request("POST", f"/api/method/{method}", data=params)

    def _json_params(self, **values: Any) -> dict[str, Any]:
        """Query parameters for a whitelisted method: containers JSON-encoded."""
        params: dict[str, Any] = {}
        for key, value in values.items():
            if value is None:
                continue
            if isinstance(value, dict | list | tuple):
                params[key] = json.dumps(value)
            else:
                params[key] = value
        return params

    def _read_for_transition(self, doctype: str, name: str) -> dict:
        doc = self.request("GET", _doc_path(doctype, name))
        current = doc.get("data", doc) if isinstance(doc, dict) else doc
        return current if isinstance(current, dict) else {}

    def submit_document(self, doctype: str, name: str) -> dict:
        """Submit a saved draft (docstatus 0 -> 1), posting its ledger entries.

        POST /api/method/frappe.client.submit

        Refused before the POST unless the document is a Draft of a
        submittable doctype (explicit document lifecycle machine). The draft is
        read first so the submit carries its latest ``modified`` stamp.
        """
        current = self._read_for_transition(doctype, name)
        state = state_of({"doctype": doctype, "name": name, **current})
        guards = Guards(doctype=doctype, name=name)
        if state is DocumentState.Draft:
            meta = self.get_doctype_meta(doctype)
            guards = Guards(
                doctype=doctype,
                name=name,
                is_submittable=bool(int(meta.get("is_submittable") or 0)),
            )
        transition(state, DocumentEvent.Submit, guards)
        return self.request(
            "POST", "/api/method/frappe.client.submit", data={"doc": current}
        )

    def cancel_document(
        self, doctype: str, name: str, modified: str | None = None
    ) -> dict:
        """Cancel a submitted document (docstatus 1 -> 2), reversing its postings.

        POST /api/method/frappe.client.cancel

        Refused before the POST unless the document is Submitted, has no
        submitted linked documents and, when ``modified`` (the stamp the caller
        read) is given, is still at that stamp.
        """
        current = self._read_for_transition(doctype, name)
        state = state_of({"doctype": doctype, "name": name, **current})
        links: list = []
        if state is DocumentState.Submitted:
            links = self._submitted_links(doctype, name)
        transition(
            state,
            DocumentEvent.Cancel,
            Guards(
                doctype=doctype,
                name=name,
                submitted_links=links,
                expected_modified=modified,
                server_modified=current.get("modified"),
            ),
        )
        return self.request(
            "POST",
            "/api/method/frappe.client.cancel",
            data={"doctype": doctype, "name": name},
        )

    def _submitted_links(self, doctype: str, name: str) -> list[dict]:
        raw = self.request(
            "GET",
            "/api/method/frappe.desk.form.linked_with.get_submitted_linked_docs",
            params={"doctype": doctype, "name": name},
        )
        msg = raw.get("message", raw) if isinstance(raw, dict) else raw
        docs = msg.get("docs", []) if isinstance(msg, dict) else (msg or [])
        return [d for d in docs if isinstance(d, dict)]

    def amend_document(self, doctype: str, name: str) -> dict:
        """Amend a cancelled document: create a new Draft with ``amended_from`` set.

        POST /api/resource/<doctype>

        Refused before the POST unless the document is Cancelled.
        """
        current = self._read_for_transition(doctype, name)
        state = state_of({"doctype": doctype, "name": name, **current})
        transition(state, DocumentEvent.Amend, Guards(doctype=doctype, name=name))
        draft = {k: v for k, v in current.items() if k not in _AMEND_DROP}
        draft = {
            k: (
                [
                    {kk: vv for kk, vv in row.items() if kk not in _AMEND_ROW_DROP}
                    for row in v
                    if isinstance(row, dict)
                ]
                if isinstance(v, list) and v and all(isinstance(r, dict) for r in v)
                else v
            )
            for k, v in draft.items()
        }
        draft["amended_from"] = name
        return self.request("POST", _doc_path(doctype), data=draft)

    def get_count(self, doctype: str, filters: list | dict | None = None) -> dict:
        """Count the documents of a DocType that match the filters.

        GET /api/method/frappe.client.get_count
        """
        return self.request(
            "GET",
            "/api/method/frappe.client.get_count",
            params=self._json_params(doctype=doctype, filters=filters),
        )

    def get_value(
        self,
        doctype: str,
        fieldname: list[str],
        filters: list | dict | str | None = None,
    ) -> dict:
        """Read selected field values of the first document matching the filters.

        GET /api/method/frappe.client.get_value

        ``filters`` may be a document name, a filter dict or a filter list.
        """
        return self.request(
            "GET",
            "/api/method/frappe.client.get_value",
            params=self._json_params(
                doctype=doctype, fieldname=fieldname, filters=filters
            ),
        )

    def set_value(self, doctype: str, name: str, fieldname: str, value: Any) -> dict:
        """Set one field of a document and save it (runs the DocType's validation).

        POST /api/method/frappe.client.set_value
        """
        return self.request(
            "POST",
            "/api/method/frappe.client.set_value",
            data={
                "doctype": doctype,
                "name": name,
                "fieldname": fieldname,
                "value": value,
            },
        )

    def rename_document(
        self, doctype: str, old_name: str, new_name: str, merge: bool = False
    ) -> dict:
        """Rename a document, updating every link to it; optionally merge into an existing one.

        POST /api/method/frappe.client.rename_doc
        """
        return self.request(
            "POST",
            "/api/method/frappe.client.rename_doc",
            data={
                "doctype": doctype,
                "old_name": old_name,
                "new_name": new_name,
                "merge": merge,
            },
        )

    def make_mapped_document(self, method: str, source_name: str) -> dict:
        """Build the next document of a business flow from a source document.

        POST /api/method/frappe.model.mapper.make_mapped_doc

        ``method`` is the dotted mapper, for example
        ``erpnext.selling.doctype.quotation.quotation.make_sales_order``. The
        result is an unsaved draft: complete it and save it with
        ``create_document``.
        """
        return self.request(
            "POST",
            "/api/method/frappe.model.mapper.make_mapped_doc",
            data={"method": method, "source_name": source_name},
        )

    def run_document_method(
        self, doctype: str, name: str, method: str, args: dict | None = None
    ) -> dict:
        """Run a whitelisted controller method of one document.

        POST /api/method/run_doc_method
        """
        return self.request(
            "POST",
            "/api/method/run_doc_method",
            data={
                "dt": doctype,
                "dn": name,
                "method": method,
                "args": json.dumps(args or {}),
            },
        )

    def get_doctype_meta(self, doctype: str) -> dict:
        """Describe a DocType's fields: name, type, label, link target and whether required.

        GET /api/method/frappe.desk.form.load.getdoctype
        """
        raw = self.request(
            "GET",
            "/api/method/frappe.desk.form.load.getdoctype",
            params={"doctype": doctype},
        )
        docs = raw.get("docs", []) if isinstance(raw, dict) else []
        meta = next((d for d in docs if d.get("name") == doctype), {})
        fields = [
            {
                "fieldname": f.get("fieldname"),
                "fieldtype": f.get("fieldtype"),
                "label": f.get("label"),
                "options": f.get("options"),
                "reqd": f.get("reqd", 0),
                "parent": f.get("parent"),
            }
            for d in docs
            for f in d.get("fields", [])
            if f.get("fieldtype") not in ("Section Break", "Column Break", "Tab Break")
        ]
        return {
            "doctype": doctype,
            "is_submittable": meta.get("is_submittable", 0),
            "istable": meta.get("istable", 0),
            "autoname": meta.get("autoname"),
            "fields": fields,
        }

    def run_report(self, report_name: str, filters: dict | None = None) -> dict:
        """Run a query or script report and return its columns and rows.

        GET /api/method/frappe.desk.query_report.run

        Runs synchronously even for reports marked "prepared" (background),
        so the rows come back in this call.
        """
        return self.request(
            "GET",
            "/api/method/frappe.desk.query_report.run",
            params=self._json_params(
                report_name=report_name,
                filters=filters or {},
                ignore_prepared_report=1,
                are_default_filters=0,
            ),
        )

    def search_link(
        self,
        doctype: str,
        txt: str,
        filters: list | dict | None = None,
        page_length: int = 10,
    ) -> dict:
        """Find documents of a DocType whose name or title fields match the text.

        GET /api/method/frappe.desk.search.search_link
        """
        return self.request(
            "GET",
            "/api/method/frappe.desk.search.search_link",
            params=self._json_params(
                doctype=doctype, txt=txt, filters=filters, page_length=page_length
            ),
        )

    def upload_file(
        self,
        file_name: str,
        content_base64: str,
        attached_to_doctype: str | None = None,
        attached_to_name: str | None = None,
        is_private: bool = True,
    ) -> dict:
        """Upload a file, optionally attaching it to a document.

        POST /api/method/upload_file
        """
        data: dict[str, Any] = {"is_private": 1 if is_private else 0}
        if attached_to_doctype:
            data["doctype"] = attached_to_doctype
        if attached_to_name:
            data["docname"] = attached_to_name
        files = {"file": (file_name, base64.b64decode(content_base64))}
        return self.request("POST", "/api/method/upload_file", data=data, files=files)
