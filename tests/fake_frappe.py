"""An in-memory stand-in for the Frappe REST surface the onboarding uses.

It answers ``Api.request`` calls: resource list/get/create/update, the
time-zone and chart-template lookups, the setup wizard and the Holiday List
weekly-off generator. Names follow the server's autoname rules for the
doctypes the onboarding creates.
"""

import json
from datetime import date, timedelta
from typing import Any
from urllib.parse import unquote

from erpnext_agent.api.api_client_base import ErpNextApiError

WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def _autoname(doctype: str, doc: dict[str, Any], abbr_of) -> str:
    if doc.get("__newname"):
        return doc.pop("__newname")
    if doctype == "Company":
        return doc["company_name"]
    if doctype == "Fiscal Year":
        return doc["year"]
    if doctype == "Address":
        return f"{doc['address_title']}-{doc['address_type']}"
    if doctype == "Bank":
        return doc["bank_name"]
    if doctype == "Account":
        return f"{doc['account_name']} - {abbr_of(doc['company'])}"
    if doctype == "Bank Account":
        return f"{doc['account_name']} - {doc['bank']}"
    if doctype == "Holiday List":
        return doc["holiday_list_name"]
    if doctype == "Department":
        return f"{doc['department_name']} - {abbr_of(doc['company'])}"
    if doctype == "Designation":
        return doc["designation_name"]
    if doctype == "Sales Stage":
        return doc["stage_name"]
    raise AssertionError(f"unexpected create of {doctype}")


class FakeFrappe:
    def __init__(self, setup_complete: bool = True):
        self.db: dict[str, dict[str, dict[str, Any]]] = {
            "Country": {"United States": {"name": "United States"}},
            "Currency": {"USD": {"name": "USD"}},
            "Installed Application": {
                "frappe": {"app_name": "frappe", "is_setup_complete": setup_complete},
                "erpnext": {"app_name": "erpnext", "is_setup_complete": setup_complete},
            },
        }
        self.writes: list[tuple[str, str]] = []
        self.wizard_args: dict[str, Any] | None = None

    def _abbr(self, company: str) -> str:
        return self.db["Company"][company]["abbr"]

    def _table(self, doctype: str) -> dict[str, dict[str, Any]]:
        return self.db.setdefault(doctype, {})

    def _list(self, doctype: str, params: dict[str, Any]) -> dict[str, Any]:
        filters = json.loads(params.get("filters") or "{}")
        rows = [
            row
            for row in self._table(doctype).values()
            if all(row.get(k) == v for k, v in filters.items())
        ]
        limit = int(params.get("limit_page_length") or 20)
        return {"data": [dict(r) for r in rows[:limit]]}

    def _create(self, doctype: str, doc: dict[str, Any]) -> dict[str, Any]:
        doc = dict(doc)
        if doctype == "Account" and doc.get("parent_account"):
            assert doc["parent_account"] in self._table("Account"), doc
        name = _autoname(doctype, doc, self._abbr)
        if name in self._table(doctype):
            raise ErpNextApiError(409, "DuplicateEntryError", [f"{name} exists"])
        doc["name"] = name
        self._table(doctype)[name] = doc
        self.writes.append(("create", f"{doctype}/{name}"))
        if doctype == "Company":
            group = f"Bank Accounts - {doc['abbr']}"
            self._table("Account")[group] = {"name": group, "is_group": 1}
        return {"data": doc}

    def _wizard(self, args: dict[str, Any]) -> dict[str, Any]:
        self.wizard_args = args
        self._create(
            "Company",
            {
                "company_name": args["company_name"],
                "abbr": args["company_abbr"],
                "default_currency": args["currency"],
                "country": args["country"],
            },
        )
        self._create(
            "Fiscal Year",
            {
                "year": args["fy_start_date"][:4],
                "year_start_date": args["fy_start_date"],
                "year_end_date": args["fy_end_date"],
                "companies": [],
            },
        )
        for app in self.db["Installed Application"].values():
            app["is_setup_complete"] = True
        return {"message": {"status": "ok"}}

    def _weekly_offs(self, doc: dict[str, Any]) -> dict[str, Any]:
        day = date.fromisoformat(doc["from_date"])
        end = date.fromisoformat(doc["to_date"])
        have = {h["holiday_date"] for h in doc.get("holidays", [])}
        rows = list(doc.get("holidays", []))
        while day <= end:
            if (
                WEEKDAYS[day.weekday()] == doc["weekly_off"]
                and day.isoformat() not in have
            ):
                rows.append({"holiday_date": day.isoformat(), "weekly_off": 1})
            day += timedelta(days=1)
        return {"docs": [{**doc, "holidays": rows}]}

    def request(self, method, endpoint, params=None, data=None, files=None):
        params = params or {}
        if endpoint.startswith("/api/resource/"):
            parts = [
                unquote(p) for p in endpoint.removeprefix("/api/resource/").split("/")
            ]
            doctype, name = parts[0], (parts[1] if len(parts) > 1 else None)
            if method == "GET" and name is None:
                return self._list(doctype, params)
            if method == "GET":
                return {"data": dict(self._table(doctype)[name])}
            if method == "POST":
                return self._create(doctype, data)
            if method == "PUT":
                self._table(doctype)[name].update(data)
                self.writes.append(("update", f"{doctype}/{name}"))
                return {"data": dict(self._table(doctype)[name])}
        if endpoint.endswith("get_timezones"):
            return {"message": {"timezones": ["America/Chicago", "UTC"]}}
        if endpoint.endswith("get_charts_for_country"):
            return {"message": ["Standard", "Standard with Numbers"]}
        if endpoint.endswith("setup_wizard.setup_complete"):
            return self._wizard(data["args"])
        if endpoint == "/api/method/run_doc_method":
            assert data["method"] == "get_weekly_off_dates"
            return self._weekly_offs(data["docs"])
        raise AssertionError(f"unexpected call {method} {endpoint}")
