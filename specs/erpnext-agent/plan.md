# CONN-ERPNEXT-AGENT — Implementation plan

Governing spec: [spec.md](spec.md). Rows: [requirements.md](requirements.md).

## Summary

This plan delivers connector identity and release metadata for the connector, reusing the SDK for shared capabilities.

## Technical Context

- **Language/Version**: Python 3.14 (floor 3.12)
- **Primary Dependencies**: scion-sdk, fastmcp
- **Storage**: N/A; the connector stores nothing
- **Testing**: pytest; the proof level each row names
- **Target Platform**: Linux containers
- **Project Type**: connector (MCP server)
- **Performance Goals**: N/A
- **Constraints**: one tool per API operation; shared capabilities come from the SDK
- **Scale/Scope**: 4 rows

## Constitution Check

- One owner per concept: pass. The connector owns one external system's calls, mappings and tools only.
- Connectors depend on the SDK and are called through arbora: pass.
- No ratchets: pass. The rows add no suppression.

## Project Structure

```text
pyproject.toml  existing
erpnext_agent/ontology/access_contracts.ttl  existing
```

## Phase 0: Research

No unknowns. Each row names the code it touches.

## Phase 1: Design

### Access-contract evidence (CONN-ERPNEXT-AGENT-R002)

Exercise the registered resource tool through MCP with a synthetic provider.
Compare each supplier and purchase-order contract field to its returned record.
A production recording and any additional source-specific status mapping remain separate work.

### Transactional invoice source prerequisite

The optional `scion_erp_guard` Frappe app is installed on the ERPNext site,
not in the MCP connector process. It commits an idempotency reservation before creation. Creation and
reconciliation lock the same claim row. The invoice and applied receipt commit
in the same Frappe POST transaction. A repeated exact claim returns the
committed receipt. A claim collision aborts the transaction; the client
reconciles before any retry. An absent claim is unknown, not proof that no
source effect occurred. The site operator binds each source user to
one tenant and grants the Sales Invoice permissions separately.

This source app is a prerequisite for SCION-SOURCE-INGEST-R006.33 through
R006.37. Local tests do not prove that a deployed site's app, hooks and
transaction isolation satisfy that contract. The connector still needs a
qualified transport, durable EG approval and receipt binding, and a real
ERPNext served test before the full workflow is complete.

### Document lifecycle machine (CONN-ERPNEXT-AGENT-R011)

Frappe stores the lifecycle as the integer `docstatus`. The connector reads that integer once, at the edge, and maps it to `DocumentState`. Every move goes through `transition(state, event, guards)` in `erpnext_agent/lifecycle.py`.

| From | Event | Guard | To |
|---|---|---|---|
| Draft | Save | none | Draft |
| Draft | Submit | doctype is submittable | Submitted |
| Submitted | Cancel | no submitted linked documents; `modified` is current | Cancelled |
| Cancelled | Amend | none | Draft (new document, `amended_from` set) |

Every other pair is refused with `IllegalTransition` before the write request. Ledger postings are irreversible, so the refusal is the only guard that acts before the posting.

Terminal states: none. The persisted field is the Frappe `docstatus` integer; `documentState` in the graph mirror is derived from it. `DOCUMENT_LIFECYCLE` is the SDK descriptor built from the same table (R011.7); `execute_governed` refuses an illegal governed write before the API call. Entry point to attach point: `erpnext_agent:connector` -> `Api.submit_document` -> `transition` (erpnext_agent/lifecycle.py) -> `ApiClientBase.request` (erpnext_agent/api/api_client_base.py). Wiring row R011.6 and hot-path proof R011.6 test it.

Types: `DocumentState` (StrEnum, three members), `DocumentEvent` (StrEnum, four members), `RefusalReason` (StrEnum, seven members), `IllegalTransition` (error with doctype, name, state, event, reason). The module carries no I/O. Cross-repo dependencies: SCION-GOVERNED-WRITEBACK-R007, SCION-CONNECTOR-CONTROL-R917 and, pending on a medulla branch, MEDULLA-ORCH-VOCAB-R811.

### Adoption of scion-sdk 0.10.0 (CONN-ERPNEXT-AGENT-R012)

- Owner. This repository, the import lines named in `CONN-ERPNEXT-AGENT-R012`. The paths belong to scion-sdk.
- Cohesion. The import edits, the pin and the lock change together and sit in one change.
- Dependency direction. The connector imports public modules of the SDK units; no import points to a private module.
- Interface depth. The connector uses the public surface only.
- Special cases. None. Every removed path takes the same replacement, with no alias.
- State. None.
- Environment. None. The pin is package metadata, not environment code.

## Phase 2: Task approach

`tasks.md` holds one task line per row, producer first.

## Complexity Tracking

None. The constitution check passed.

## Build contract

The repository pre-commit hooks apply: `ruff-format`, `connector-standard`, `secrets`, `tests-fast`. Each row names its proving test. No suppression and no duplicate implementation.

## Production caller chain

1. `CONN-ERPNEXT-AGENT-R001`: the erpnext-mcp console script (scion_sdk.cli:serve) loads erpnext_agent:connector, and the version is read at import from erpnext_agent/api_client.py:8 (__version__ = _v("erpnext-agent")) using installed package metadata, while the bump configuration edits pyproject.toml.
2. `CONN-ERPNEXT-AGENT-R002`: the erpnext-mcp console script loads erpnext_agent:connector (erpnext_agent/__init__.py:89), whose SDK tool surface (scion_sdk.mcp.method_tools.register_method_tools) serves Api.list_documents (erpnext_agent/api/api_client_resource.py) as the typed tool erpnext_list_documents.
3. `CONN-ERPNEXT-AGENT-R003`: the erpnext-mcp console script loads erpnext_agent:connector (erpnext_agent/__init__.py:89); the declared Supplier contract in erpnext_agent/ontology/access_contracts.ttl is answered by the typed tool erpnext_list_documents calling Api.list_documents (erpnext_agent/api/api_client_resource.py).
4. `CONN-ERPNEXT-AGENT-R004`: the erpnext-mcp console script loads erpnext_agent:connector (erpnext_agent/__init__.py:89), and the served tool erpnext_list_documents returns the Supplier and PurchaseOrder fields pinned in erpnext_agent/ontology/access_contracts.ttl.
5. `CONN-ERPNEXT-AGENT-R005`: the erpnext-mcp console script loads erpnext_agent:connector (erpnext_agent/__init__.py), and the SDK tool surface registers one typed tool per public method of Api (erpnext_agent/api/api_client_resource.py); each method sends one Frappe REST call through ApiClientBase.request.
6. `CONN-ERPNEXT-AGENT-R006`: every typed tool calls an Api method, which calls ApiClientBase.request (erpnext_agent/api/api_client_base.py); a 4xx/5xx response raises frappe_error(status, body).
7. `CONN-ERPNEXT-AGENT-R007`: scion_sdk.access_contract.parse_access_contracts reads erpnext_agent/ontology/access_contracts.ttl; each contract's operation is served by the server that scion_sdk._connector_serve.build_server builds.
8. `CONN-ERPNEXT-AGENT-R008`: the erpnext-mcp console script loads erpnext_agent:connector, and the SDK tool surface registers one typed tool per public method of Api (erpnext_agent/api_client.py), which inherits ApiHr (erpnext_agent/api/api_client_hr.py); each method sends its Frappe or HR-app call through ApiClientBase.request.
9. `CONN-ERPNEXT-AGENT-R009`: the erpnext-mcp console script loads erpnext_agent:connector, and the SDK tool surface registers one typed tool per public method of Api, which inherits ApiCrm (erpnext_agent/api/api_client_crm.py); mapped drafts come from frappe.model.mapper.make_mapped_doc and are saved through /api/resource.
10. `CONN-ERPNEXT-AGENT-R010`: the erpnext-mcp console script loads erpnext_agent:connector, and the SDK tool surface registers the onboarding tools from Api, which inherits ApiOnboarding (erpnext_agent/api/api_client_onboarding.py); plan, apply and verify call erpnext_agent.onboarding over the typed client.
11. `CONN-ERPNEXT-AGENT-R011`: the erpnext-mcp console script loads erpnext_agent:connector, whose SDK tool surface registers `erpnext_submit_document`, `erpnext_cancel_document` and `erpnext_amend_document` from `Api` (erpnext_agent/api/api_client_resource.py:103,117); each calls `transition` (erpnext_agent/lifecycle.py) before `ApiClientBase.request`.

## Cross-repo seams

none. The cited owner rows are library capabilities the connector calls in process; spec.md names them.

### Amendments

- 2026-11-06: ERPNext is the CRM and HR system of record (owner). Rows `CONN-ERPNEXT-AGENT-R008` (HR operations), `CONN-ERPNEXT-AGENT-R009` (built-in CRM operations; the separate Frappe CRM app is not targeted, one owner of leads) and `CONN-ERPNEXT-AGENT-R010` (repeatable business onboarding: validate, dry run, apply on confirm, verify, idempotent) extend the typed-operation surface of `CONN-ERPNEXT-AGENT-R005`. Methods target the Frappe, ERPNext and HR app version-16 whitelisted methods and doctypes.
- 2026-11-06: document lifecycle as an explicit state machine (organization constitution Article XXXI). Row `CONN-ERPNEXT-AGENT-R011` and its children R011.1 to R011.7 extend `CONN-ERPNEXT-AGENT-R005` (typed submit and cancel) with guards and an amend tool. The ontology half is `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R009`.
