"""Typed CRM and onboarding-record operations: each maps to its Frappe REST call."""

import json
from unittest.mock import patch

import pytest

from erpnext_agent.api_client import Api

MAPPER = ("POST", "/api/method/frappe.model.mapper.make_mapped_doc")


def _client() -> Api:
    return Api(base_url="http://localhost")


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R009")
def test_lead_capture_update_qualify_and_list():
    client = _client()
    with patch.object(client, "request") as req:
        client.create_lead("Ada", "C", company_name="Prospect Inc", source="Website")
        req.assert_called_with(
            "POST",
            "/api/resource/Lead",
            data={
                "first_name": "Ada",
                "company_name": "Prospect Inc",
                "source": "Website",
                "company": "C",
                "status": "Lead",
            },
        )
        client.update_lead("CRM-LEAD-1", {"status": "Interested"})
        req.assert_called_with(
            "PUT", "/api/resource/Lead/CRM-LEAD-1", data={"status": "Interested"}
        )
        client.qualify_lead("CRM-LEAD-1", qualified_on="2026-11-06")
        req.assert_called_with(
            "PUT",
            "/api/resource/Lead/CRM-LEAD-1",
            data={"qualification_status": "Qualified", "qualified_on": "2026-11-06"},
        )
        client.list_leads(status="Open")
        assert json.loads(req.call_args.kwargs["params"]["filters"]) == {
            "status": "Open"
        }


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R009")
def test_opportunity_from_lead_stage_and_lost():
    client = _client()
    mapped = {"message": {"doctype": "Opportunity", "party_name": "CRM-LEAD-1"}}
    with patch.object(client, "request", side_effect=[mapped, {"data": {}}]) as req:
        client.create_opportunity_from_lead(
            "CRM-LEAD-1", "C", currency="USD", sales_stage="Proposal"
        )
    assert req.call_args_list[0].args == MAPPER
    assert req.call_args_list[0].kwargs["data"] == {
        "method": "erpnext.crm.doctype.lead.lead.make_opportunity",
        "source_name": "CRM-LEAD-1",
    }
    assert req.call_args_list[1].args == ("POST", "/api/resource/Opportunity")
    assert req.call_args_list[1].kwargs["data"] == {
        "doctype": "Opportunity",
        "party_name": "CRM-LEAD-1",
        "company": "C",
        "currency": "USD",
        "sales_stage": "Proposal",
    }
    with patch.object(client, "request") as req:
        client.update_opportunity_stage("CRM-OPP-1", "Negotiation", probability=60)
        req.assert_called_with(
            "PUT",
            "/api/resource/Opportunity/CRM-OPP-1",
            data={"sales_stage": "Negotiation", "probability": 60},
        )
        client.declare_opportunity_lost("CRM-OPP-1", ["Price"], "Too expensive")
        args, kwargs = req.call_args
        assert args == ("POST", "/api/method/run_doc_method")
        assert kwargs["data"]["method"] == "declare_enquiry_lost"
        assert json.loads(kwargs["data"]["args"]) == {
            "lost_reasons_list": [{"lost_reason": "Price"}],
            "competitors": [],
            "detailed_reason": "Too expensive",
        }
        client.create_opportunity_lost_reason("Price")
        req.assert_called_with(
            "POST",
            "/api/resource/Opportunity%20Lost%20Reason",
            data={"lost_reason": "Price"},
        )
        client.list_opportunities(sales_stage="Proposal")
        assert req.call_args.args == ("GET", "/api/resource/Opportunity")


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R009")
def test_customer_from_lead_and_from_opportunity():
    client = _client()
    for convert, method in (
        (client.make_customer_from_lead, "erpnext.crm.doctype.lead.lead.make_customer"),
        (
            client.make_customer_from_opportunity,
            "erpnext.crm.doctype.opportunity.opportunity.make_customer",
        ),
    ):
        mapped = {"message": {"doctype": "Customer", "customer_name": "Prospect Inc"}}
        with patch.object(client, "request", side_effect=[mapped, {}]) as req:
            convert("SRC-1", customer_group="Commercial", tax_id="T-1")
        assert req.call_args_list[0].kwargs["data"]["method"] == method
        assert req.call_args_list[1].args == ("POST", "/api/resource/Customer")
        assert req.call_args_list[1].kwargs["data"] == {
            "doctype": "Customer",
            "customer_name": "Prospect Inc",
            "customer_group": "Commercial",
            "tax_id": "T-1",
        }


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R009")
def test_pipeline_stages_types_communication_and_follow_up():
    client = _client()
    with patch.object(client, "request") as req:
        client.create_sales_stage("Proposal")
        req.assert_called_with(
            "POST", "/api/resource/Sales%20Stage", data={"stage_name": "Proposal"}
        )
        client.list_sales_stages()
        assert req.call_args.args == ("GET", "/api/resource/Sales%20Stage")
        client.create_opportunity_type("Consulting")
        req.assert_called_with(
            "POST",
            "/api/resource/Opportunity%20Type",
            data={"__newname": "Consulting"},
        )
        client.list_opportunity_types()
        assert req.call_args.args == ("GET", "/api/resource/Opportunity%20Type")
        client.log_communication("Lead", "CRM-LEAD-1", "Intro call", "Discussed scope")
        args, kwargs = req.call_args
        assert args == ("POST", "/api/resource/Communication")
        assert kwargs["data"]["communication_medium"] == "Phone"
        assert kwargs["data"]["reference_name"] == "CRM-LEAD-1"
        client.create_follow_up("Lead", "CRM-LEAD-1", "Send proposal", "a@b.invalid")
        args, kwargs = req.call_args
        assert args == ("POST", "/api/resource/ToDo")
        assert kwargs["data"]["reference_type"] == "Lead"
        assert kwargs["data"]["status"] == "Open"
        client.list_follow_ups(reference_doctype="Lead")
        assert json.loads(req.call_args.kwargs["params"]["filters"]) == {
            "reference_type": "Lead",
            "status": "Open",
        }
        client.close_follow_up("TODO-1")
        req.assert_called_with(
            "PUT", "/api/resource/ToDo/TODO-1", data={"status": "Closed"}
        )


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R010")
def test_company_books_address_bank_and_tax_id_records():
    client = _client()
    with patch.object(client, "request") as req:
        client.create_company("zz Co", "ZZ", "USD", "United States", tax_id="T")
        args, kwargs = req.call_args
        assert args == ("POST", "/api/resource/Company")
        assert (
            kwargs["data"]["create_chart_of_accounts_based_on"] == "Standard Template"
        )
        assert kwargs["data"]["chart_of_accounts"] == "Standard"
        client.create_fiscal_year("2026", "2026-01-01", "2026-12-31", ["zz Co"])
        assert req.call_args.kwargs["data"]["companies"] == [{"company": "zz Co"}]
        client.create_address(
            "zz Co", "1 Way", "Town", "United States", "Company", "zz Co"
        )
        sent = req.call_args.kwargs["data"]
        assert sent["is_your_company_address"] == 1
        assert sent["links"] == [{"link_doctype": "Company", "link_name": "zz Co"}]
        client.create_bank("zz Bank")
        req.assert_called_with(
            "POST", "/api/resource/Bank", data={"bank_name": "zz Bank"}
        )
        client.create_bank_account("Op", "zz Bank", "zz Co", account="Op - ZZ")
        sent = req.call_args.kwargs["data"]
        assert sent["is_company_account"] == 1 and sent["account"] == "Op - ZZ"
        client.set_tax_id("Company", "zz Co", "T-2")
        req.assert_called_with(
            "POST",
            "/api/method/frappe.client.set_value",
            data={
                "doctype": "Company",
                "name": "zz Co",
                "fieldname": "tax_id",
                "value": "T-2",
            },
        )
        with pytest.raises(ValueError):
            client.set_tax_id("Item", "x", "T")
        client.list_timezones()
        req.assert_called_with(
            "GET", "/api/method/frappe.core.doctype.user.user.get_timezones"
        )
        client.list_chart_of_accounts_templates("United States")
        assert req.call_args.kwargs["params"] == {
            "country": "United States",
            "with_standard": 1,
        }
