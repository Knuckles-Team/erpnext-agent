# Usage — MCP / API / CLI

`erpnext-agent` exposes the same capability three ways: as **MCP tools** an agent
calls, as a **Python API** (`Api`) you import, and as a **command-line** entry point
for the MCP and agent servers. The full DocType / RPC surface is summarized in
[Overview](overview.md).

## As an MCP server

Once [deployed](deployment.md), the server registers two action-dispatch tools that
cover the entire ERPNext / Frappe REST and whitelisted-RPC surface. Each tool takes
an `action` plus a JSON `params_json` payload:

| Tool | Actions |
|---|---|
| `erpnext_agent_authentication` | `login`, `logout`, `get_logged_user`, `get_version` |
| `erpnext_agent_resource` | `get_document`, `create_document`, `update_document`, `delete_document`, `list_documents`, `call_method` |

Example agent prompts that map onto these tools:

- *"List the 10 most recent Sales Invoices"* → `erpnext_agent_resource` / `list_documents`
- *"Fetch the Customer document named 'ACME Corp'"* → `erpnext_agent_resource` / `get_document`
- *"Who is the currently logged-in user?"* → `erpnext_agent_authentication` / `get_logged_user`
- *"Run the whitelisted method `frappe.ping`"* → `erpnext_agent_resource` / `call_method`

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

Construct the client explicitly when you want to pass credentials inline:

```python
from erpnext_agent.api_client import Api

api = Api(
    base_url="https://your-erpnext:8000",
    token="your_api_key:your_api_secret",
    verify=False,                  # self-signed homelab certificate
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

```bash
# MCP server (stdio by default; --transport streamable-http for a network server)
erpnext-mcp --help
erpnext-mcp --transport streamable-http --host 0.0.0.0 --port 8000

# Pydantic-AI agent server (wraps the MCP tools in a conversational agent)
erpnext-agent --help
erpnext-agent --host 0.0.0.0 --port 8001 --mcp-url http://localhost:8000/mcp
```

See [Deployment](deployment.md) for the full transport, reverse-proxy, and agent
server configuration.
