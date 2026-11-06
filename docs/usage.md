# Usage — MCP / API / CLI

`erpnext-agent` exposes the same capability three ways: as **MCP tools** an agent
calls, as a **Python API** (`Api`) the operator import, and as a **command-line** entry point
[Overview](overview.md).

## As an MCP server

Once [deployed](deployment.md), the server serves one typed tool per Frappe
operation, plus `erpnext_ingest` for the knowledge graph:

| Tool | Frappe call |
|---|---|
| `erpnext_list_documents`, `erpnext_get_document`, `erpnext_create_document`, `erpnext_update_document`, `erpnext_delete_document` | `/api/resource/<doctype>[/<name>]` |
| `erpnext_submit_document`, `erpnext_cancel_document` | `frappe.client.submit`, `frappe.client.cancel` |
| `erpnext_get_count`, `erpnext_get_value`, `erpnext_set_value`, `erpnext_rename_document` | `frappe.client.*` |
| `erpnext_make_mapped_document` | `frappe.model.mapper.make_mapped_doc` (quotation to order, order to invoice, lead to opportunity) |
| `erpnext_run_document_method` | `run_doc_method` |
| `erpnext_get_doctype_meta` | `frappe.desk.form.load.getdoctype` |
| `erpnext_run_report` | `frappe.desk.query_report.run` |
| `erpnext_search_link` | `frappe.desk.search.search_link` |
| `erpnext_upload_file` | `upload_file` |
| `erpnext_call_method` | any other whitelisted method |
| `erpnext_get_version`, `erpnext_get_logged_user`, `erpnext_login`, `erpnext_logout` | version and session |
| HR: `erpnext_create_employee` ... `erpnext_relieve_employee`, departments, designations, holiday lists, attendance, check-ins, leave, salary and payroll (31 tools) | `/api/resource/<HR doctype>`, `run_doc_method` (`get_weekly_off_dates`, `fill_employee_details`, `create_salary_slips`, `submit_salary_slips`), `hrms...mark_employee_attendance`, `hrms...get_leave_balance_on` |
| CRM: `erpnext_create_lead` ... `erpnext_close_follow_up`: leads, opportunities, sales stages, opportunity types, lost reasons, conversion to customer, communication log and follow-ups (19 tools) | `/api/resource/<CRM doctype>`, `make_mapped_doc` (`lead.make_opportunity`, `lead.make_customer`, `opportunity.make_customer`), `run_doc_method` (`declare_enquiry_lost`) |
| Onboarding: `erpnext_get_setup_status`, `erpnext_list_timezones`, `erpnext_list_chart_of_accounts_templates`, `erpnext_complete_setup_wizard`, `erpnext_create_company`, `erpnext_create_fiscal_year`, `erpnext_create_address`, `erpnext_create_bank`, `erpnext_create_bank_account`, `erpnext_set_tax_id` | `Installed Application`, `get_timezones`, `get_charts_for_country`, `setup_wizard.setup_complete` (only with `confirm`), `/api/resource/<doctype>` |
| `erpnext_plan_business_onboarding`, `erpnext_apply_business_onboarding`, `erpnext_verify_business_onboarding` | repeatable onboarding: validate and dry run, apply on `confirm` (idempotent), verify |

Example agent prompts:

- *"Bill the accepted quotation and record the payment"* → skill `erpnext-order-to-cash`
- *"What do customers owe us?"* → `erpnext_run_report` `Accounts Receivable`
- *"How many units of item X are in Stores?"* → `erpnext_get_value` on `Bin`
- *"Run the whitelisted method `frappe.ping`"* → `erpnext_call_method`
- *"Approve Ada's leave request"* → `erpnext_approve_leave_application`
- *"Set up our company"* → `erpnext_plan_business_onboarding`, then `erpnext_apply_business_onboarding` after approval

A refused call returns the server's reason, for example
`API error: 417 LinkValidationError: Could not find Customer: X`.

## As a Python API

`Api` is a tolerant `requests`-based REST/RPC facade. Build one directly, or use
`get_client()` to read connection settings from the environment.

```python
from erpnext_agent.auth import get_client

api = get_client()                 # reads ERPNEXT_URL / ERPNEXT_TOKEN from the env

# Reads
user = api.get_logged_user()
version = api.get_version()
invoices = api.list_documents(
    "Sales Invoice",
    fields=["name", "customer", "grand_total"],
    limit=10,
)
customer = api.get_document("Customer", "ACME Corp")
```

Build the client explicitly when the operator want to pass credentials inline:

```python
from erpnext_agent.api_client import Api

api = Api(
    base_url="https://your-erpnext:8000",
    token="your_api_key:your_api_secret",
)
```

### Writes

Document writes and arbitrary whitelisted RPC calls are available on the same client:

```python
api.create_document("Note", {"title": "Standup", "content": "Notes for today"})
api.update_document("Note", "Standup", {"content": "Updated notes"})
api.delete_document("Note", "Standup")

# Any whitelisted server method — covers custom server functions
api.call_method("frappe.client.get_count", {"doctype": "Customer"})
```

## As a CLI

Two console scripts are installed:

See [Deployment](deployment.md) for the full transport, reverse-proxy, and agent
server configuration.
