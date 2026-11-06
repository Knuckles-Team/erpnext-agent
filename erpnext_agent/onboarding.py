"""Repeatable, idempotent business onboarding for an ERPNext site.

One input document (the onboarding spec, see the ``erpnext-business-onboarding``
skill's ``references/onboarding-spec.yaml``) describes a company: legal name,
abbreviation, country, currency, fiscal year, time zone, chart of accounts
template, tax ID, address, bank, the HR basics (holiday list, departments,
designations) and the CRM pipeline (sales stages, opportunity types).

:func:`plan` validates the spec against the server and lists every record as
``exists``, ``create`` or ``update`` without writing anything. :func:`apply`
runs only the ``create`` and ``update`` steps, in order, so running it again
changes nothing. :func:`verify` re-plans and reports whatever is still missing.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from erpnext_agent.api._docs import data_of

COA_METHOD = (
    "erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts"
    ".get_charts_for_country"
)
TIMEZONES_METHOD = "frappe.core.doctype.user.user.get_timezones"
SETUP_COMPLETE_METHOD = "frappe.desk.page.setup_wizard.setup_wizard.setup_complete"
SINGLE_VALUE_METHOD = "/api/method/frappe.client.get_single_value"

MODES = ("auto", "setup_wizard", "company")


def _rows(response: Any) -> list[dict[str, Any]]:
    rows = data_of(response)
    return rows if isinstance(rows, list) else []


def _message(response: Any) -> Any:
    return response.get("message") if isinstance(response, dict) else response


def _first(client: Any, doctype: str, filters: dict[str, Any], fields: list[str]):
    """The first record of ``doctype`` matching ``filters``, or ``None``."""
    rows = _rows(
        client.list_documents(doctype, filters=filters, fields=fields, limit=1)
    )
    return rows[0] if rows else None


def setup_status(client: Any) -> dict[str, Any]:
    """Whether the setup wizard is complete, per installed app, plus the companies.

    The per-app flags live in the ``Installed Applications`` single document;
    a site whose table is still empty falls back to the System Settings flag.
    """
    installed = data_of(
        client.get_document("Installed Applications", "Installed Applications")
    )
    rows = (
        installed.get("installed_applications") if isinstance(installed, dict) else None
    )
    apps = [
        {
            "app_name": a.get("app_name"),
            "app_version": a.get("app_version"),
            "is_setup_complete": bool(a.get("is_setup_complete")),
        }
        for a in rows or []
    ]
    by_app = {a["app_name"]: a["is_setup_complete"] for a in apps}
    if "frappe" in by_app and "erpnext" in by_app:
        complete = by_app["frappe"] and by_app["erpnext"]
    else:
        flag = _message(
            client.request(
                "GET",
                SINGLE_VALUE_METHOD,
                params={"doctype": "System Settings", "field": "setup_complete"},
            )
        )
        complete = bool(int(flag or 0))
    companies = _rows(
        client.list_documents(
            "Company",
            fields=["name", "abbr", "country", "default_currency"],
            limit=100,
        )
    )
    return {"setup_complete": complete, "apps": apps, "companies": companies}


def _required(spec: dict[str, Any]) -> list[str]:
    company = spec.get("company") or {}
    fiscal = spec.get("fiscal_year") or {}
    missing = [
        f"company.{key}"
        for key in ("name", "abbr", "country", "currency", "chart_of_accounts")
        if not company.get(key)
    ]
    missing += [
        f"fiscal_year.{key}"
        for key in ("start_date", "end_date")
        if not fiscal.get(key)
    ]
    if not spec.get("time_zone"):
        missing.append("time_zone")
    return [f"missing input: {field}" for field in missing]


def _date_errors(spec: dict[str, Any]) -> list[str]:
    fiscal = spec.get("fiscal_year") or {}
    errors: list[str] = []
    try:
        start = date.fromisoformat(str(fiscal.get("start_date")))
        end = date.fromisoformat(str(fiscal.get("end_date")))
    except ValueError:
        return ["fiscal_year dates must be YYYY-MM-DD"]
    if end <= start:
        errors.append("fiscal_year.end_date must be after start_date")
    holiday = (spec.get("hr") or {}).get("holiday_list") or {}
    if holiday:
        for key in ("name", "from_date", "to_date"):
            if not holiday.get(key):
                errors.append(f"missing input: hr.holiday_list.{key}")
    return errors


def validate(client: Any, spec: dict[str, Any]) -> list[str]:
    """Every reason the spec cannot be applied on this server (empty when valid)."""
    errors = _required(spec)
    if errors:
        return errors
    errors += _date_errors(spec)
    company = spec["company"]
    country = company["country"]
    if not _first(client, "Country", {"name": country}, ["name"]):
        errors.append(f"unknown country: {country}")
    currency = company["currency"]
    if not _first(client, "Currency", {"name": currency}, ["name"]):
        errors.append(f"unknown currency: {currency}")
    zones = _message(client.list_timezones()) or {}
    zone_list = zones.get("timezones", []) if isinstance(zones, dict) else zones
    if spec["time_zone"] not in (zone_list or []):
        errors.append(f"unknown time zone: {spec['time_zone']}")
    charts = _message(client.list_chart_of_accounts_templates(country)) or []
    if company["chart_of_accounts"] not in charts:
        errors.append(
            f"chart of accounts template {company['chart_of_accounts']!r} "
            f"is not offered for {country}"
        )
    existing = _first(client, "Company", {"name": company["name"]}, ["name", "abbr"])
    if existing and existing.get("abbr") != company["abbr"]:
        errors.append(
            f"company {company['name']!r} exists with abbreviation "
            f"{existing.get('abbr')!r}, not {company['abbr']!r}"
        )
    return errors


def _step(
    key: str,
    doctype: str,
    name: str,
    status: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    step: dict[str, Any] = {
        "step": key,
        "doctype": doctype,
        "name": name,
        "status": status,
    }
    if payload is not None and status in ("create", "update"):
        step["payload"] = payload
    return step


def _wizard_args(spec: dict[str, Any]) -> dict[str, Any]:
    company, fiscal = spec["company"], spec["fiscal_year"]
    admin = spec.get("admin") or {}
    args = {
        "language": spec.get("language") or "English",
        "country": company["country"],
        "timezone": spec["time_zone"],
        "currency": company["currency"],
        "company_name": company["name"],
        "company_abbr": company["abbr"],
        "chart_of_accounts": company["chart_of_accounts"],
        "fy_start_date": fiscal["start_date"],
        "fy_end_date": fiscal["end_date"],
        "setup_demo": 0,
        "enable_telemetry": 0,
    }
    if admin.get("email"):
        args["email"] = admin["email"]
        args["full_name"] = admin.get("full_name") or ""
    return args


def _company_steps(
    client: Any, spec: dict[str, Any], wizard: bool
) -> list[dict[str, Any]]:
    company, fiscal = spec["company"], spec["fiscal_year"]
    name = company["name"]
    steps: list[dict[str, Any]] = []
    existing = _first(client, "Company", {"name": name}, ["name", "tax_id"])
    if wizard:
        steps.append(
            _step("setup_wizard", "Setup Wizard", name, "create", _wizard_args(spec))
        )
    elif existing:
        steps.append(_step("company", "Company", name, "exists"))
    else:
        steps.append(
            _step(
                "company",
                "Company",
                name,
                "create",
                {
                    "company_name": name,
                    "abbr": company["abbr"],
                    "default_currency": company["currency"],
                    "country": company["country"],
                    "chart_of_accounts": company["chart_of_accounts"],
                    "create_chart_of_accounts_based_on": "Standard Template",
                    "tax_id": company.get("tax_id"),
                    "domain": company.get("domain"),
                },
            )
        )
    steps.append(_fiscal_year_step(client, fiscal, name, wizard))
    tax_id = company.get("tax_id")
    if not tax_id:
        return steps
    if wizard:
        steps.append(_step("tax_id", "Company", name, "after_setup_wizard"))
    elif existing and existing.get("tax_id") != tax_id:
        steps.append(_step("tax_id", "Company", name, "update", {"tax_id": tax_id}))
    elif existing:
        steps.append(_step("tax_id", "Company", name, "exists"))
    return steps


def _fiscal_year_step(
    client: Any, fiscal: dict[str, Any], company: str, wizard: bool
) -> dict[str, Any]:
    start, end = fiscal["start_date"], fiscal["end_date"]
    label = fiscal.get("name") or (
        start[:4] if start[:4] == end[:4] else f"{start[:4]}-{end[:4]}"
    )
    found = _first(
        client,
        "Fiscal Year",
        {"year_start_date": start, "year_end_date": end},
        ["name"],
    )
    if not found:
        if wizard:
            return _step("fiscal_year", "Fiscal Year", label, "by_setup_wizard")
        return _step(
            "fiscal_year",
            "Fiscal Year",
            label,
            "create",
            {
                "year": label,
                "year_start_date": start,
                "year_end_date": end,
                "companies": [{"company": company}],
            },
        )
    doc = data_of(client.get_document("Fiscal Year", found["name"]))
    rows = (doc.get("companies") or []) if isinstance(doc, dict) else []
    linked = {r.get("company") for r in rows}
    if rows and company not in linked:
        return _step(
            "fiscal_year",
            "Fiscal Year",
            found["name"],
            "update",
            {"companies": [*rows, {"company": company}]},
        )
    return _step("fiscal_year", "Fiscal Year", found["name"], "exists")


def _address_step(client: Any, spec: dict[str, Any]) -> list[dict[str, Any]]:
    address = spec.get("address") or {}
    if not address:
        return []
    company = spec["company"]["name"]
    title = address.get("title") or company
    kind = address.get("address_type") or "Billing"
    found = _first(
        client,
        "Address",
        {"address_title": title, "address_type": kind},
        ["name"],
    )
    if found:
        return [_step("address", "Address", found["name"], "exists")]
    payload = {
        "address_title": title,
        "address_type": kind,
        "address_line1": address.get("address_line1"),
        "address_line2": address.get("address_line2"),
        "city": address.get("city"),
        "state": address.get("state"),
        "pincode": address.get("pincode"),
        "country": address.get("country") or spec["company"]["country"],
        "email_id": address.get("email_id"),
        "phone": address.get("phone"),
        "is_your_company_address": 1,
        "is_primary_address": 1,
        "links": [{"link_doctype": "Company", "link_name": company}],
    }
    payload = {k: v for k, v in payload.items() if v is not None}
    return [_step("address", "Address", f"{title}-{kind}", "create", payload)]


def _bank_steps(client: Any, spec: dict[str, Any]) -> list[dict[str, Any]]:
    bank = spec.get("bank") or {}
    if not bank:
        return []
    company = spec["company"]
    steps: list[dict[str, Any]] = []
    bank_name = bank["bank_name"]
    found = _first(client, "Bank", {"name": bank_name}, ["name"])
    steps.append(
        _step(
            "bank",
            "Bank",
            bank_name,
            "exists" if found else "create",
            {"bank_name": bank_name},
        )
    )
    account_name = bank["account_name"]
    ledger = bank.get("gl_account") or f"{account_name} - {company['abbr']}"
    if not bank.get("gl_account"):
        found = _first(client, "Account", {"name": ledger}, ["name"])
        steps.append(
            _step(
                "bank_ledger",
                "Account",
                ledger,
                "exists" if found else "create",
                {
                    "account_name": account_name,
                    "parent_account": f"Bank Accounts - {company['abbr']}",
                    "company": company["name"],
                    "account_type": "Bank",
                    "account_currency": company["currency"],
                    "is_group": 0,
                },
            )
        )
    found = _first(
        client,
        "Bank Account",
        {"account_name": account_name, "bank": bank_name, "company": company["name"]},
        ["name"],
    )
    payload = {
        "account_name": account_name,
        "bank": bank_name,
        "company": company["name"],
        "account": ledger,
        "is_company_account": 1,
        "is_default": 1 if bank.get("is_default", True) else 0,
        "bank_account_no": bank.get("bank_account_no"),
        "iban": bank.get("iban"),
        "branch_code": bank.get("branch_code"),
    }
    steps.append(
        _step(
            "bank_account",
            "Bank Account",
            found["name"] if found else f"{account_name} - {bank_name}",
            "exists" if found else "create",
            {k: v for k, v in payload.items() if v is not None},
        )
    )
    return steps


def _hr_steps(client: Any, spec: dict[str, Any]) -> list[dict[str, Any]]:
    hr = spec.get("hr") or {}
    company = spec["company"]
    steps: list[dict[str, Any]] = []
    holiday = hr.get("holiday_list") or {}
    if holiday:
        name = holiday["name"]
        found = _first(client, "Holiday List", {"name": name}, ["name"])
        steps.append(
            _step(
                "holiday_list",
                "Holiday List",
                name,
                "exists" if found else "create",
                {
                    "holiday_list_name": name,
                    "from_date": holiday["from_date"],
                    "to_date": holiday["to_date"],
                    "weekly_off": holiday.get("weekly_off"),
                    "holidays": [
                        {"holiday_date": h["date"], "description": h["description"]}
                        for h in holiday.get("holidays") or []
                    ],
                },
            )
        )
        current = _first(
            client, "Company", {"name": company["name"]}, ["default_holiday_list"]
        )
        linked = bool(current) and current.get("default_holiday_list") == name
        steps.append(
            _step(
                "default_holiday_list",
                "Company",
                company["name"],
                "exists" if linked else "update",
                {"default_holiday_list": name},
            )
        )
    for department in hr.get("departments") or []:
        found = _first(
            client,
            "Department",
            {"department_name": department, "company": company["name"]},
            ["name"],
        )
        steps.append(
            _step(
                "department",
                "Department",
                found["name"] if found else f"{department} - {company['abbr']}",
                "exists" if found else "create",
                {"department_name": department, "company": company["name"]},
            )
        )
    for designation in hr.get("designations") or []:
        found = _first(client, "Designation", {"name": designation}, ["name"])
        steps.append(
            _step(
                "designation",
                "Designation",
                designation,
                "exists" if found else "create",
                {"designation_name": designation},
            )
        )
    return steps


def _crm_steps(client: Any, spec: dict[str, Any]) -> list[dict[str, Any]]:
    crm = spec.get("crm") or {}
    steps: list[dict[str, Any]] = []
    for stage in crm.get("sales_stages") or []:
        found = _first(client, "Sales Stage", {"name": stage}, ["name"])
        steps.append(
            _step(
                "sales_stage",
                "Sales Stage",
                stage,
                "exists" if found else "create",
                {"stage_name": stage},
            )
        )
    for kind in crm.get("opportunity_types") or []:
        found = _first(client, "Opportunity Type", {"name": kind}, ["name"])
        steps.append(
            _step(
                "opportunity_type",
                "Opportunity Type",
                kind,
                "exists" if found else "create",
                {"__newname": kind},
            )
        )
    return steps


def plan(client: Any, spec: dict[str, Any]) -> dict[str, Any]:
    """Validate the spec, then list each record as exists, create or update (no writes)."""
    mode = spec.get("mode") or "auto"
    if mode not in MODES:
        return {"valid": False, "errors": [f"mode must be one of {MODES}"], "steps": []}
    errors = validate(client, spec)
    status = setup_status(client)
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "setup_complete": status["setup_complete"],
            "steps": [],
        }
    wizard = mode == "setup_wizard" or (mode == "auto" and not status["setup_complete"])
    if wizard and status["setup_complete"]:
        wizard = False
    steps = (
        _company_steps(client, spec, wizard)
        + _address_step(client, spec)
        + _bank_steps(client, spec)
        + _hr_steps(client, spec)
        + _crm_steps(client, spec)
    )
    pending = [s for s in steps if s["status"] in ("create", "update")]
    return {
        "valid": True,
        "errors": [],
        "setup_complete": status["setup_complete"],
        "mode": "setup_wizard" if wizard else "company",
        "steps": steps,
        "pending": len(pending),
    }


def _run_step(client: Any, step: dict[str, Any]) -> Any:
    key, payload = step["step"], step.get("payload", {})
    if key == "setup_wizard":
        return client.call_method(SETUP_COMPLETE_METHOD, {"args": payload})
    if key == "holiday_list":
        return client.create_holiday_list(
            payload["holiday_list_name"],
            payload["from_date"],
            payload["to_date"],
            holidays=payload.get("holidays"),
            weekly_off=payload.get("weekly_off"),
        )
    if step["status"] == "update":
        return client.update_document(step["doctype"], step["name"], payload)
    return client.create_document(step["doctype"], payload)


def apply(client: Any, spec: dict[str, Any]) -> dict[str, Any]:
    """Create or update every pending record of the plan, in order, then verify."""
    planned = plan(client, spec)
    if not planned["valid"]:
        return {"applied": [], "plan": planned, "verified": False}
    applied: list[dict[str, Any]] = []
    for step in planned["steps"]:
        if step["status"] not in ("create", "update"):
            continue
        _run_step(client, step)
        applied.append(
            {"step": step["step"], "doctype": step["doctype"], "name": step["name"]}
        )
        if step["step"] == "setup_wizard":
            # The wizard created the company and fiscal year: re-plan the rest.
            rest = apply(client, {**spec, "mode": "company"})
            applied += rest["applied"]
            return {"applied": applied, "plan": planned, **verify(client, spec)}
    return {"applied": applied, "plan": planned, **verify(client, spec)}


def verify(client: Any, spec: dict[str, Any]) -> dict[str, Any]:
    """Re-plan in company mode: verified when nothing is left to create or update."""
    replanned = plan(client, {**spec, "mode": "company"})
    missing = [
        {"step": s["step"], "doctype": s["doctype"], "name": s["name"]}
        for s in replanned["steps"]
        if s["status"] in ("create", "update")
    ]
    return {
        "verified": replanned["valid"] and not missing,
        "missing": missing,
        "errors": replanned["errors"],
    }
