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

## Phase 2: Task approach

`tasks.md` holds one task line per row, producer first.

## Complexity Tracking

None. The constitution check passed.

## Build contract

The repository pre-commit hooks apply: `ruff-format`, `connector-standard`, `secrets`, `tests-fast`. Each row names its proving test. No suppression and no duplicate implementation.

## Production caller chain

1. `CONN-ERPNEXT-AGENT-R001`: the erpnext-mcp console script (scion_sdk.cli:serve) loads erpnext_agent:connector, and the version is read at import from erpnext_agent/api_client.py:8 (__version__ = _v("erpnext-agent")) using installed package metadata, while the bump configuration edits pyproject.toml.
2. `CONN-ERPNEXT-AGENT-R002`: the erpnext-mcp console script loads erpnext_agent:connector (erpnext_agent/__init__.py:89), whose tools erpnext_agent.mcp_server register register_resource_tools (erpnext_agent/mcp/mcp_resource.py:13) defining erpnext_agent_resource at mcp_resource.py:16, which dispatches to Api.list_documents (erpnext_agent/api/api_client_resource.py:63).
3. `CONN-ERPNEXT-AGENT-R003`: the erpnext-mcp console script loads erpnext_agent:connector (erpnext_agent/__init__.py:89); the declared Supplier contract in erpnext_agent/ontology/access_contracts.ttl is answered by erpnext_agent_resource (erpnext_agent/mcp/mcp_resource.py:16) calling Api.list_documents (erpnext_agent/api/api_client_resource.py:63).
4. `CONN-ERPNEXT-AGENT-R004`: the erpnext-mcp console script loads erpnext_agent:connector (erpnext_agent/__init__.py:89), and the served tool erpnext_agent_resource (erpnext_agent/mcp/mcp_resource.py:16) returns the Supplier and PurchaseOrder fields pinned in erpnext_agent/ontology/access_contracts.ttl.

## Cross-repo seams

none. The cited owner rows are library capabilities the connector calls in process; spec.md names them.
