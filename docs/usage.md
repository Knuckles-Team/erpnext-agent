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

Example agent prompts:

- *"Bill the accepted quotation and record the payment"* → skill `erpnext-order-to-cash`
- *"What do customers owe us?"* → `erpnext_run_report` `Accounts Receivable`
- *"How many units of item X are in Stores?"* → `erpnext_get_value` on `Bin`
- *"Run the whitelisted method `frappe.ping`"* → `erpnext_call_method`

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
