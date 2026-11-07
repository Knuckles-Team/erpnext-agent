"""Typed Frappe operations: each maps to one documented REST call."""

import json
from unittest.mock import patch

import pytest

from erpnext_agent.api.api_client_base import ErpNextApiError, frappe_error
from erpnext_agent.api_client import Api


def _client() -> Api:
    return Api(base_url="http://localhost")


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R005")
def test_submit_reads_the_current_draft_then_submits_it():
    client = _client()
    draft = {"doctype": "Sales Invoice", "name": "SINV-1", "modified": "t"}
    meta = {"docs": [{"name": "Sales Invoice", "is_submittable": 1}]}
    with patch.object(
        client, "request", side_effect=[{"data": draft}, meta, {"message": {}}]
    ) as req:
        client.submit_document("Sales Invoice", "SINV-1")
    assert req.call_args_list[0].args == ("GET", "/api/resource/Sales%20Invoice/SINV-1")
    assert req.call_args_list[-1].args == ("POST", "/api/method/frappe.client.submit")
    assert req.call_args_list[-1].kwargs == {"data": {"doc": draft}}


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R005")
def test_lifecycle_and_value_operations_map_to_frappe_client():
    client = _client()
    submitted = {"data": {"docstatus": 1, "modified": "t"}}
    with patch.object(
        client, "request", side_effect=[submitted, {"message": {"docs": []}}, {}]
    ) as req:
        client.cancel_document("Payment Entry", "PAY-1")
        req.assert_called_with(
            "POST",
            "/api/method/frappe.client.cancel",
            data={"doctype": "Payment Entry", "name": "PAY-1"},
        )
    with patch.object(client, "request") as req:
        client.get_count("Employee", {"company": "C"})
        req.assert_called_with(
            "GET",
            "/api/method/frappe.client.get_count",
            params={"doctype": "Employee", "filters": json.dumps({"company": "C"})},
        )
        client.get_value("Bin", ["actual_qty"], {"item_code": "I"})
        req.assert_called_with(
            "GET",
            "/api/method/frappe.client.get_value",
            params={
                "doctype": "Bin",
                "fieldname": json.dumps(["actual_qty"]),
                "filters": json.dumps({"item_code": "I"}),
            },
        )
        client.set_value("Task", "TASK-1", "status", "Completed")
        req.assert_called_with(
            "POST",
            "/api/method/frappe.client.set_value",
            data={
                "doctype": "Task",
                "name": "TASK-1",
                "fieldname": "status",
                "value": "Completed",
            },
        )
        client.rename_document("Customer", "A", "B")
        req.assert_called_with(
            "POST",
            "/api/method/frappe.client.rename_doc",
            data={
                "doctype": "Customer",
                "old_name": "A",
                "new_name": "B",
                "merge": False,
            },
        )


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R005")
def test_flow_report_and_search_operations():
    client = _client()
    with patch.object(client, "request") as req:
        client.make_mapped_document("erpnext.x.make_sales_order", "QTN-1")
        req.assert_called_with(
            "POST",
            "/api/method/frappe.model.mapper.make_mapped_doc",
            data={"method": "erpnext.x.make_sales_order", "source_name": "QTN-1"},
        )
        client.run_report("General Ledger", {"company": "C"})
        req.assert_called_with(
            "GET",
            "/api/method/frappe.desk.query_report.run",
            params={
                "report_name": "General Ledger",
                "filters": json.dumps({"company": "C"}),
                "ignore_prepared_report": 1,
                "are_default_filters": 0,
            },
        )
        client.search_link("Customer", "acme")
        req.assert_called_with(
            "GET",
            "/api/method/frappe.desk.search.search_link",
            params={"doctype": "Customer", "txt": "acme", "page_length": 10},
        )
        client.run_document_method(
            "Opportunity", "OPP-1", "declare_enquiry_lost", {"a": 1}
        )
        req.assert_called_with(
            "POST",
            "/api/method/run_doc_method",
            data={
                "dt": "Opportunity",
                "dn": "OPP-1",
                "method": "declare_enquiry_lost",
                "args": '{"a": 1}',
            },
        )
        client.upload_file("a.txt", "eno=", "Sales Invoice", "SINV-1")
        args, kwargs = req.call_args
        assert args == ("POST", "/api/method/upload_file")
        assert kwargs["data"] == {
            "is_private": 1,
            "doctype": "Sales Invoice",
            "docname": "SINV-1",
        }
        assert kwargs["files"]["file"][0] == "a.txt"


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R005")
def test_doctype_meta_is_trimmed_to_fields():
    client = _client()
    raw = {
        "docs": [
            {
                "name": "Lead",
                "is_submittable": 0,
                "fields": [
                    {
                        "fieldname": "lead_name",
                        "fieldtype": "Data",
                        "label": "Name",
                        "reqd": 1,
                    },
                    {"fieldname": "sb", "fieldtype": "Section Break"},
                ],
            }
        ]
    }
    with patch.object(client, "request", return_value=raw):
        meta = client.get_doctype_meta("Lead")
    assert meta["is_submittable"] == 0
    assert [f["fieldname"] for f in meta["fields"]] == ["lead_name"]
    assert meta["fields"][0]["reqd"] == 1


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R006")
def test_refusal_carries_the_server_reason_not_the_traceback():
    body = json.dumps(
        {
            "exc_type": "LinkValidationError",
            "exc": "Traceback (most recent call last): secret frames",
            "_server_messages": json.dumps(
                [json.dumps({"message": "Could not find <b>Gender</b>: X"})]
            ),
        }
    )
    err = frappe_error(417, body)
    assert isinstance(err, ErpNextApiError)
    assert str(err) == "API error: 417 LinkValidationError: Could not find Gender: X"
    assert "Traceback" not in str(err)
    assert (
        str(frappe_error(502, "<html>bad gateway</html>"))
        == "API error: 502: no server message"
    )


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.4")
def test_amend_is_served_as_its_own_tool(monkeypatch):
    import asyncio

    from fastmcp import Client
    from scion_sdk._connector_serve import build_server

    monkeypatch.setenv("ERPNEXT_URL", "https://service.invalid")
    monkeypatch.setenv("AUTH_TYPE", "none")
    _, mcp = build_server("erpnext_agent", command_args=["--transport", "stdio"])

    async def names():
        async with Client(mcp) as c:
            return {t.name for t in await c.list_tools()}

    assert "erpnext_amend_document" in asyncio.run(names())
