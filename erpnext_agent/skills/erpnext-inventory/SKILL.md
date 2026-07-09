---
name: erpnext-inventory
skill_type: skill
description: >-
  Item-catalog and stock operations on ERPNext (Frappe) via the erpnext-agent MCP
  server — list, read, and create Item, Customer and Supplier DocTypes, and natively
  ingest them into the knowledge graph as typed :Item / :Customer / :Supplier nodes.
  Use when the agent must look up a product by item_code, review the catalog by
  item_group/stock_uom, resolve a party for an order, or push catalog/master data into
  the KG. Do NOT use for order/invoice financials (use erpnext-accounting) or employee
  records (use erpnext-hr).
license: MIT
tags: [erpnext, frappe, inventory, item, catalog, rest-api, mcp]
metadata:
  author: Genius
  version: '0.1.0'
---
# ERPNext Inventory & Master Data

Domain-typed access to the ERPNext catalog / party master DocTypes (`Item`,
`Customer`, `Supplier`) via the Frappe REST resource API, plus native ingestion of
those records into the epistemic-graph knowledge graph.

## When to use
- Look up an Item by `item_code`, or browse the catalog by `item_group` / `stock_uom`.
- Resolve or create a `Customer` / `Supplier` master record for an order.
- Ingest the catalog / party masters into the KG as typed `:Item` / `:Customer` /
  `:Supplier` nodes (the targets of `:contains` / `:orderedBy` / `:suppliedBy` links).

## When NOT to use
- Sales/purchase orders and invoices, totals, reconciliation → `erpnext-accounting`.
- Employees, departments → `erpnext-hr`.
- Warehouse-level stock ledger entries the typed recipes don't cover → the generic
  `erpnext_agent_resource` tool against `Stock Ledger Entry` / `Bin`.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`erpnext-agent`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `ERPNEXT_URL` | ✅ | Frappe/ERPNext base URL (alias `ERPNEXT_AGENT_BASE_URL`) |
| `ERPNEXT_TOKEN` | one of | `api_key:api_secret` token or Bearer |
| `ERPNEXT_AGENT_USERNAME` / `ERPNEXT_AGENT_PASSWORD` | one of | Basic-auth / login fallback |
| `ERPNEXT_AGENT_SSL_VERIFY` | optional | TLS verification toggle |

## Tools & actions
Prefer the **condensed** tools; each takes `action` + a `params_json` **JSON string**.

| Condensed tool | Actions |
|----------------|---------|
| `erpnext_agent_resource` | `list_documents`, `get_document`, `create_document`, `update_document`, `delete_document`, `call_method` |
| `erpnext_ingest` | ingest a DocType (`doctype` + `params_json`) into the KG |

### Key parameters
- `doctype` — `"Item"`, `"Customer"`, or `"Supplier"`.
- `name` — Frappe primary key (for `Item`, defaults to `item_code`).
- `filters` — e.g. `[["item_group","=","Products"]]`.
- `fields` — e.g. `["name","item_name","item_group","stock_uom"]`.

## Recipes (`params_json`)
List stock items in a group:
```json
{"doctype":"Item","params_json":"{\"filters\":[[\"item_group\",\"=\",\"Products\"]],\"fields\":[\"name\",\"item_name\",\"item_group\",\"stock_uom\"],\"limit_page_length\":50}"}
```
Get one Customer master:
```json
{"doctype":"Customer","params_json":"{\"name\":\"Acme Corp\"}"}
```
Ingest the whole Item catalog into the KG:
```json
{"doctype":"Item","params_json":"{\"fields\":[\"name\",\"item_code\",\"item_name\",\"item_group\",\"stock_uom\"],\"limit_page_length\":200}"}
```

## Gotchas
- `params_json` is a **string** of JSON — serialize it (including the nested one for
  `erpnext_agent_resource`).
- An `Item`'s Frappe `name` is normally its `item_code`; the KG node id keys off
  `item_code` so ordered items dedupe against the catalog.
- `Customer.customer_name` / `Supplier.supplier_name` are the display names; the
  primary key `name` may differ (naming series). Request both if you need the label.
- Unbounded `list_documents` is slow — always set `fields` + a sane `limit_page_length`.

## Related
- **KG plumbing:** `erpnext_ingest` writes typed `:Item`/`:Customer`/`:Supplier` nodes.
- Orders & invoices → `erpnext-accounting`; HR → `erpnext-hr`.
