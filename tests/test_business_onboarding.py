"""Business onboarding: validate, dry-run plan, apply once, verify, re-run changes nothing."""

import copy
from unittest.mock import patch

import pytest
from fake_frappe import FakeFrappe

from erpnext_agent.api_client import Api

SPEC = {
    "mode": "company",
    "company": {
        "name": "zz-validation-co",
        "abbr": "ZZV",
        "country": "United States",
        "currency": "USD",
        "chart_of_accounts": "Standard",
        "tax_id": "00-0000000",
    },
    "fiscal_year": {"start_date": "2026-01-01", "end_date": "2026-12-31"},
    "time_zone": "America/Chicago",
    "address": {
        "title": "zz-validation-co",
        "address_line1": "1 Test Way",
        "city": "Testville",
    },
    "bank": {"bank_name": "zz-validation-bank", "account_name": "Operating"},
    "hr": {
        "holiday_list": {
            "name": "zz-validation-holidays",
            "from_date": "2026-01-01",
            "to_date": "2026-01-31",
            "weekly_off": "Sunday",
            "holidays": [{"date": "2026-01-01", "description": "New Year"}],
        },
        "departments": ["Operations"],
        "designations": ["zz-validation-engineer"],
    },
    "crm": {"sales_stages": ["zz-validation-stage"], "opportunity_types": ["zz-type"]},
}


def _client(server: FakeFrappe) -> Api:
    client = Api(base_url="http://localhost")
    patch.object(client, "request", side_effect=server.request).start()
    return client


@pytest.fixture(autouse=True)
def _stop_patches():
    yield
    patch.stopall()


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R010")
def test_plan_validates_inputs_against_the_server():
    client = _client(FakeFrappe())
    bad = copy.deepcopy(SPEC)
    bad["company"].update(country="Atlantis", currency="XXX", chart_of_accounts="X")
    bad["time_zone"] = "Mars/Olympus"
    plan = client.plan_business_onboarding(bad)
    assert plan["valid"] is False
    assert plan["steps"] == []
    joined = " ".join(plan["errors"])
    for word in ("Atlantis", "XXX", "Mars/Olympus", "'X'"):
        assert word in joined
    missing = client.plan_business_onboarding({"company": {"name": "a"}})
    assert "missing input: company.abbr" in missing["errors"]
    assert "missing input: time_zone" in missing["errors"]


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R010")
def test_dry_run_writes_nothing_and_lists_every_record():
    server = FakeFrappe()
    client = _client(server)
    plan = client.plan_business_onboarding(SPEC)
    assert plan["valid"] and plan["mode"] == "company"
    assert server.writes == []
    statuses = {(s["step"], s["name"]): s["status"] for s in plan["steps"]}
    assert statuses[("company", "zz-validation-co")] == "create"
    assert statuses[("department", "Operations - ZZV")] == "create"
    assert statuses[("bank_ledger", "Operating - ZZV")] == "create"
    assert plan["pending"] == len(plan["steps"])
    refused = client.apply_business_onboarding(SPEC)
    assert refused["applied"] == [] and server.writes == []


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R010")
def test_apply_creates_once_verifies_and_rerun_is_a_no_op():
    server = FakeFrappe()
    client = _client(server)
    first = client.apply_business_onboarding(SPEC, confirm=True)
    assert first["verified"] is True, first["missing"]
    created = {w[1] for w in server.writes if w[0] == "create"}
    assert {
        "Company/zz-validation-co",
        "Fiscal Year/2026",
        "Address/zz-validation-co-Billing",
        "Bank/zz-validation-bank",
        "Account/Operating - ZZV",
        "Bank Account/Operating - zz-validation-bank",
        "Holiday List/zz-validation-holidays",
        "Department/Operations - ZZV",
        "Designation/zz-validation-engineer",
        "Sales Stage/zz-validation-stage",
        "Opportunity Type/zz-type",
    } <= created
    company = server.db["Company"]["zz-validation-co"]
    assert company["default_holiday_list"] == "zz-validation-holidays"
    holidays = server.db["Holiday List"]["zz-validation-holidays"]["holidays"]
    assert len(holidays) == 5  # New Year plus four Sundays of January 2026
    writes = len(server.writes)
    again = client.apply_business_onboarding(SPEC, confirm=True)
    assert again["applied"] == [] and again["verified"] is True
    assert len(server.writes) == writes
    replan = client.plan_business_onboarding(SPEC)
    assert replan["pending"] == 0
    assert {s["status"] for s in replan["steps"]} == {"exists"}


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R010")
def test_changed_tax_id_and_unlinked_fiscal_year_are_updates():
    server = FakeFrappe()
    client = _client(server)
    client.apply_business_onboarding(SPEC, confirm=True)
    server.db["Fiscal Year"]["2026"]["companies"] = [{"company": "Other Co"}]
    changed = copy.deepcopy(SPEC)
    changed["company"]["tax_id"] = "11-1111111"
    plan = client.plan_business_onboarding(changed)
    updates = {s["step"]: s for s in plan["steps"] if s["status"] == "update"}
    assert set(updates) == {"tax_id", "fiscal_year"}
    assert updates["fiscal_year"]["payload"]["companies"][-1] == {
        "company": "zz-validation-co"
    }
    result = client.apply_business_onboarding(changed, confirm=True)
    assert result["verified"] is True
    assert server.db["Company"]["zz-validation-co"]["tax_id"] == "11-1111111"


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R010")
def test_incomplete_wizard_runs_setup_complete_only_when_planned():
    server = FakeFrappe(setup_complete=False)
    client = _client(server)
    auto = dict(SPEC, mode="auto")
    plan = client.plan_business_onboarding(auto)
    assert plan["mode"] == "setup_wizard" and plan["setup_complete"] is False
    assert plan["steps"][0]["step"] == "setup_wizard"
    assert plan["steps"][0]["payload"]["company_abbr"] == "ZZV"
    # Company mode never calls the wizard, even when it is not complete.
    company_mode = client.plan_business_onboarding(SPEC)
    assert all(s["step"] != "setup_wizard" for s in company_mode["steps"])
    result = client.apply_business_onboarding(auto, confirm=True)
    assert server.wizard_args["company_name"] == "zz-validation-co"
    assert server.wizard_args["setup_demo"] == 0
    assert result["verified"] is True
    assert client.get_setup_status()["setup_complete"] is True


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R010")
def test_setup_wizard_tool_refuses_without_confirm():
    client = Api(base_url="http://localhost")
    with patch.object(client, "request") as req:
        refused = client.complete_setup_wizard(
            "C",
            "C",
            "United States",
            "USD",
            "UTC",
            "2026-01-01",
            "2026-12-31",
            "Standard",
        )
        assert refused["status"] == "not_run"
        req.assert_not_called()
        client.complete_setup_wizard(
            "C",
            "C",
            "United States",
            "USD",
            "UTC",
            "2026-01-01",
            "2026-12-31",
            "Standard",
            confirm=True,
        )
        args, kwargs = req.call_args
        assert args == (
            "POST",
            "/api/method/frappe.desk.page.setup_wizard.setup_wizard.setup_complete",
        )
        assert kwargs["data"]["args"]["company_abbr"] == "C"
        assert kwargs["data"]["args"]["timezone"] == "UTC"


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R010")
def test_empty_app_table_falls_back_to_the_system_settings_flag():
    server = FakeFrappe(setup_complete=False)
    server.db["Installed Applications"]["Installed Applications"][
        "installed_applications"
    ] = []
    client = _client(server)
    assert client.get_setup_status()["setup_complete"] is False
    server.system_setup_complete = True
    assert client.get_setup_status()["setup_complete"] is True
