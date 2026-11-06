"""Typed business-onboarding operations: setup wizard, company, books and bank.

Each public method is one Frappe operation and is served as its own typed
tool. ``plan_business_onboarding``, ``apply_business_onboarding`` and
``verify_business_onboarding`` run the repeatable onboarding of
:mod:`erpnext_agent.onboarding` over these operations.
"""

from typing import Any

from erpnext_agent import onboarding
from erpnext_agent.api._docs import compact
from erpnext_agent.api.api_client_crm import ApiCrm
from erpnext_agent.api.api_client_hr import ApiHr
from erpnext_agent.api.api_client_resource import _doc_path

_TAX_ID_DOCTYPES = ("Company", "Customer", "Supplier")


class ApiOnboarding(ApiHr, ApiCrm):
    def get_setup_status(self) -> dict:
        """Report whether the setup wizard is complete (per app) and list the companies.

        GET /api/resource/Installed Applications, frappe.client.get_single_value
        (System Settings setup_complete) and /api/resource/Company
        """
        return onboarding.setup_status(self)

    def list_timezones(self) -> dict:
        """List the time zones the server accepts.

        GET /api/method/frappe.core.doctype.user.user.get_timezones
        """
        return self.request("GET", f"/api/method/{onboarding.TIMEZONES_METHOD}")

    def list_chart_of_accounts_templates(self, country: str) -> dict:
        """List the chart-of-accounts templates offered for a country (plus Standard).

        GET /api/method/erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_charts_for_country
        """
        return self.request(
            "GET",
            f"/api/method/{onboarding.COA_METHOD}",
            params={"country": country, "with_standard": 1},
        )

    def complete_setup_wizard(
        self,
        company_name: str,
        company_abbr: str,
        country: str,
        currency: str,
        timezone: str,
        fy_start_date: str,
        fy_end_date: str,
        chart_of_accounts: str,
        confirm: bool = False,
        language: str = "English",
        full_name: str | None = None,
        email: str | None = None,
    ) -> dict:
        """Complete the site's one-time setup wizard: first company, books and regional settings.

        POST /api/method/frappe.desk.page.setup_wizard.setup_wizard.setup_complete

        Irreversible and site-wide: it runs only with ``confirm`` true, after
        the owner approved the dry-run plan. A completed wizard answers ok and
        changes nothing.
        """
        if not confirm:
            return {
                "status": "not_run",
                "reason": "confirm must be true; run plan_business_onboarding first",
            }
        args = compact(
            {
                "language": language,
                "country": country,
                "timezone": timezone,
                "currency": currency,
                "company_name": company_name,
                "company_abbr": company_abbr,
                "chart_of_accounts": chart_of_accounts,
                "fy_start_date": fy_start_date,
                "fy_end_date": fy_end_date,
                "full_name": full_name,
                "email": email,
                "setup_demo": 0,
                "enable_telemetry": 0,
            }
        )
        return self.request(
            "POST",
            f"/api/method/{onboarding.SETUP_COMPLETE_METHOD}",
            data={"args": args},
        )

    def create_company(
        self,
        company_name: str,
        abbr: str,
        default_currency: str,
        country: str,
        chart_of_accounts: str = "Standard",
        tax_id: str | None = None,
        domain: str | None = None,
        parent_company: str | None = None,
        is_group: bool = False,
    ) -> dict:
        """Create a Company with its chart of accounts from a template (an extra or test company).

        POST /api/resource/Company
        """
        doc = compact(
            {
                "company_name": company_name,
                "abbr": abbr,
                "default_currency": default_currency,
                "country": country,
                "create_chart_of_accounts_based_on": "Standard Template",
                "chart_of_accounts": chart_of_accounts,
                "tax_id": tax_id,
                "domain": domain,
                "parent_company": parent_company,
                "is_group": 1 if is_group else 0,
            }
        )
        return self.request("POST", _doc_path("Company"), data=doc)

    def create_fiscal_year(
        self,
        year: str,
        year_start_date: str,
        year_end_date: str,
        companies: list[str] | None = None,
    ) -> dict:
        """Create a Fiscal Year, optionally limited to some companies.

        POST /api/resource/Fiscal Year
        """
        doc = {
            "year": year,
            "year_start_date": year_start_date,
            "year_end_date": year_end_date,
            "companies": [{"company": c} for c in companies or []],
        }
        return self.request("POST", _doc_path("Fiscal Year"), data=doc)

    def create_address(
        self,
        address_title: str,
        address_line1: str,
        city: str,
        country: str,
        link_doctype: str,
        link_name: str,
        address_type: str = "Billing",
        address_line2: str | None = None,
        state: str | None = None,
        pincode: str | None = None,
        email_id: str | None = None,
        phone: str | None = None,
    ) -> dict:
        """Create an Address linked to a Company, Customer, Supplier or Lead.

        POST /api/resource/Address

        A Company link marks it as one of our own addresses.
        """
        doc = compact(
            {
                "address_title": address_title,
                "address_type": address_type,
                "address_line1": address_line1,
                "address_line2": address_line2,
                "city": city,
                "state": state,
                "pincode": pincode,
                "country": country,
                "email_id": email_id,
                "phone": phone,
                "is_your_company_address": 1 if link_doctype == "Company" else 0,
                "links": [{"link_doctype": link_doctype, "link_name": link_name}],
            }
        )
        return self.request("POST", _doc_path("Address"), data=doc)

    def create_bank(self, bank_name: str, swift_number: str | None = None) -> dict:
        """Create a Bank master record.

        POST /api/resource/Bank
        """
        doc = compact({"bank_name": bank_name, "swift_number": swift_number})
        return self.request("POST", _doc_path("Bank"), data=doc)

    def create_bank_account(
        self,
        account_name: str,
        bank: str,
        company: str | None = None,
        account: str | None = None,
        is_company_account: bool = True,
        is_default: bool = False,
        bank_account_no: str | None = None,
        iban: str | None = None,
        branch_code: str | None = None,
    ) -> dict:
        """Create a Bank Account; a company account names its GL ledger in ``account``.

        POST /api/resource/Bank Account
        """
        doc = compact(
            {
                "account_name": account_name,
                "bank": bank,
                "company": company,
                "account": account,
                "is_company_account": 1 if is_company_account else 0,
                "is_default": 1 if is_default else 0,
                "bank_account_no": bank_account_no,
                "iban": iban,
                "branch_code": branch_code,
            }
        )
        return self.request("POST", _doc_path("Bank Account"), data=doc)

    def set_tax_id(self, doctype: str, name: str, tax_id: str) -> dict:
        """Set the tax ID of a Company, Customer or Supplier.

        POST /api/method/frappe.client.set_value
        """
        if doctype not in _TAX_ID_DOCTYPES:
            raise ValueError(f"doctype must be one of {_TAX_ID_DOCTYPES}")
        return self.set_value(doctype, name, "tax_id", tax_id)

    def plan_business_onboarding(self, spec: dict[str, Any]) -> dict:
        """Dry run: validate an onboarding spec and list what exists and what would be created.

        GET /api/resource/<doctype> and GET lookups only: nothing is written. Checks country, currency, time zone and chart template on the
        server, then lists each record (company, fiscal year, tax ID, address,
        bank, holiday list, departments, designations, sales stages,
        opportunity types) as exists, create or update.
        """
        return onboarding.plan(self, spec)

    def apply_business_onboarding(
        self, spec: dict[str, Any], confirm: bool = False
    ) -> dict:
        """Apply an approved onboarding plan: create only what is missing, then verify.

        POST /api/resource/<doctype> per missing record (PUT per out-of-date one).

        Runs only with ``confirm`` true. Idempotent: a second run creates
        nothing. Uses the setup wizard only when the plan's mode is
        setup_wizard (wizard not complete and spec mode auto or setup_wizard).
        """
        if not confirm:
            return {
                "applied": [],
                "plan": onboarding.plan(self, spec),
                "verified": False,
                "reason": "dry run: confirm must be true to apply",
            }
        return onboarding.apply(self, spec)

    def verify_business_onboarding(self, spec: dict[str, Any]) -> dict:
        """Check that every record of an onboarding spec exists as specified.

        GET /api/resource/<doctype> lookups only; reports each record still missing or out of date.
        """
        return onboarding.verify(self, spec)
