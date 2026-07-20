# Erpnext Hr

Human-resources operations on ERPNext (Frappe) via the erpnext-agent MCP server — list, read, and create Employee (and Department) DocTypes, and natively ingest them into the knowledge graph as typed :Employee / :OrgUnit nodes with :memberOf links. Use when the agent must look up an employee by name/company, review an org unit's headcount, or push HR master data into the KG. Do NOT use for order/invoice financials (use erpnext-accounting) or the item/party catalog (use erpnext-inventory).

# ERPNext HR

Domain-typed access to the ERPNext HR master DocTypes (`Employee`, `Department`) via
the Frappe REST resource API, plus native ingestion of those records into the
epistemic-graph knowledge graph.

## When to use
- Look up an `Employee` by `name` / `employee_name`, or by `company` / `department`.
- Review an org unit's members or an employee's `designation` / `status`.
- Ingest employees into the KG as typed `:Employee` nodes linked `:memberOf` an
  `:OrgUnit` (Department).

## When NOT to use
- Sales/purchase orders, invoices, totals → `erpnext-accounting`.
- Item catalog, customers, suppliers → `erpnext-inventory`.
- Payroll runs / salary slips the typed recipes don't cover → the generic
  `erpnext_agent_resource` tool against `Salary Slip` / `Payroll Entry`.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`erpnext-agent`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `ERPNEXT_URL` | ✅ | Frappe/ERPNext base URL |
| `ERPNEXT_TOKEN` | one of | `api_key:api_secret` token or Bearer |
| `ERPNEXT_AGENT_USERNAME` / `ERPNEXT_AGENT_PASSWORD` | one of | Basic-auth / login fallback |
| `TLS_PROFILE` / `TLS_PROFILES_REF` | optional | Named runtime trust profile and secret-backed catalog; verification is mandatory |

## Tools & actions
Prefer the **condensed** tools; each takes `action` + a `params_json` **JSON string**.

| Condensed tool | Actions |
|----------------|---------|
| `erpnext_agent_resource` | `list_documents`, `get_document`, `create_document`, `update_document`, `delete_document`, `call_method` |
| `erpnext_ingest` | ingest a DocType (`doctype` + `params_json`) into the KG |

### Key parameters
- `doctype` — `"Employee"` (or `"Department"`).
- `name` — Frappe primary key (Employee id, e.g. `HR-EMP-00001`).
- `filters` — e.g. `[["company","=","Acme"],["status","=","Active"]]`.
- `fields` — e.g. `["name","employee_name","department","designation","status"]`.

## Recipes (`params_json`)
List active employees in a company:
```json
{"doctype":"Employee","params_json":"{\"filters\":[[\"company\",\"=\",\"Acme\"],[\"status\",\"=\",\"Active\"]],\"fields\":[\"name\",\"employee_name\",\"department\",\"designation\"],\"limit_page_length\":50}"}
```
Get one Employee by id:
```json
{"doctype":"Employee","params_json":"{\"name\":\"HR-EMP-00001\"}"}
```
Ingest all employees into the KG (with department links):
```json
{"doctype":"Employee","params_json":"{\"fields\":[\"name\",\"employee_name\",\"department\",\"designation\",\"company\",\"status\"],\"limit_page_length\":200}"}
```

## Gotchas
- `params_json` is a **string** of JSON — serialize it (including the nested one for
  `erpnext_agent_resource`).
- An `Employee`'s Frappe `name` is the employee id, not the person's name — the KG
  node keeps `employee_name` as a separate property.
- The `:memberOf` → `:OrgUnit` link is only emitted when `department` is present, so
  request `department` in `fields` for the org graph.
- `status` is a choice value (`Active`, `Inactive`, `Left`); filter on it explicitly.

## Related
- **KG plumbing:** `erpnext_ingest` writes typed `:Employee`/`:OrgUnit` nodes + links.
- Accounting → `erpnext-accounting`; catalog/parties → `erpnext-inventory`.
