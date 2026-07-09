---
name: erpnext-accounting
skill_type: skill
description: >-
  Accounts-receivable/payable operations on ERPNext (Frappe) via the erpnext-agent
  MCP server — list, read, and create Sales Order, Purchase Order, Sales Invoice and
  Purchase Invoice DocTypes, and natively ingest them into the knowledge graph as
  typed :SalesOrder / :PurchaseOrder / :Invoice nodes. Use when the agent must review
  open orders, reconcile invoices by grand_total/status, or push order-to-cash /
  procure-to-pay state into the KG. Do NOT use for stock/item catalog work (use
  erpnext-inventory) or employee/HR records (use erpnext-hr).
license: MIT
tags: [erpnext, frappe, accounting, erp, invoice, rest-api, mcp]
metadata:
  author: Genius
  version: '0.1.0'
---
# ERPNext Accounting

Domain-typed access to the ERPNext **order-to-cash** and **procure-to-pay** DocTypes
(`Sales Order`, `Purchase Order`, `Sales Invoice`, `Purchase Invoice`) via the Frappe
REST resource API, plus native ingestion of those records into the epistemic-graph
knowledge graph.

## When to use
- List / triage open Sales Orders or Purchase Orders (by `status`, `customer`, `supplier`).
- Fetch a single order or invoice by its Frappe `name` (primary key).
- Create a draft order/invoice, or reconcile invoices by `grand_total` / `docstatus`.
- Ingest orders/invoices into the KG as typed `:SalesOrder` / `:PurchaseOrder` /
  `:Invoice` nodes with `:orderedBy` / `:suppliedBy` / `:contains` links.

## When NOT to use
- Stock levels, warehouses, or the Item catalog → `erpnext-inventory`.
- Employees, departments, leave → `erpnext-hr`.
- Arbitrary DocType CRUD the typed recipes don't cover → the generic
  `erpnext_agent_resource` tool with an explicit `doctype`.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`erpnext-agent`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `ERPNEXT_URL` | ✅ | Frappe/ERPNext base URL (alias `ERPNEXT_AGENT_BASE_URL`) |
| `ERPNEXT_TOKEN` | one of | `api_key:api_secret` token (Frappe `token` auth) or Bearer |
| `ERPNEXT_AGENT_USERNAME` / `ERPNEXT_AGENT_PASSWORD` | one of | Basic-auth / login fallback |
| `ERPNEXT_AGENT_SSL_VERIFY` | optional | TLS verification toggle |

`MCP_TOOL_MODE` (`condensed`|`verbose`|`both`) selects the condensed surface (used
below) vs. the 1:1 verbose tools.

## Tools & actions
Prefer the **condensed** tools; each takes `action` + a `params_json` **JSON string**.

| Condensed tool | Actions |
|----------------|---------|
| `erpnext_agent_resource` | `list_documents`, `get_document`, `create_document`, `update_document`, `delete_document`, `call_method` |
| `erpnext_ingest` | ingest a DocType (`doctype` + `params_json`) into the KG |

### Key parameters
- `doctype` — e.g. `"Sales Order"`, `"Sales Invoice"` (required for resource actions).
- `name` — Frappe primary key, required for `get_document` / `update_document`.
- `filters` — Frappe filter list, e.g. `[["status","=","To Deliver and Bill"]]`.
- `fields` — field list to project, e.g. `["name","customer","grand_total","status"]`.
- `limit_page_length` / `limit_start` — pagination.

## Recipes (`params_json`)
List open Sales Orders (few fields):
```json
{"doctype":"Sales Order","params_json":"{\"filters\":[[\"status\",\"=\",\"To Deliver and Bill\"]],\"fields\":[\"name\",\"customer\",\"grand_total\",\"status\"],\"limit_page_length\":25}"}
```
Get one Sales Invoice by name:
```json
{"doctype":"Sales Invoice","params_json":"{\"name\":\"ACC-SINV-2026-00001\"}"}
```
Ingest all Purchase Orders into the KG:
```json
{"doctype":"Purchase Order","params_json":"{\"fields\":[\"name\",\"supplier\",\"grand_total\",\"docstatus\",\"transaction_date\"],\"limit_page_length\":100}"}
```

## Gotchas
- `params_json` is a **string** of JSON, not an object — serialize it (and the inner
  `params_json` for `erpnext_agent_resource`).
- Frappe `docstatus` is `0`=Draft, `1`=Submitted, `2`=Cancelled — filter on it, not on
  a free-text state.
- Amounts live on `grand_total` (rounded → `rounded_total`); `list_documents` returns
  only the fields you request in `fields` plus `name` — always request `grand_total`.
- The KG mapping keys Items off `item_code`; make sure `fields` includes the child
  `items` table (or omit `fields` to get the full document) if you want line-item links.

## Related
- **KG plumbing:** `erpnext_ingest` pushes records natively as typed nodes — use it
  for ingestion, not for the operational list/read recipes above.
- Catalog & stock → `erpnext-inventory`; HR → `erpnext-hr`.
