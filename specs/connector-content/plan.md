# CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT — Implementation plan

Governing spec: [spec.md](spec.md). Rows: [requirements.md](requirements.md).

## Summary

`pyproject.toml` declares `erpnext-mcp` as the connector identity. `create_mcp_server` resolves the packaged content of `erpnext_agent` from it.

## Technical Context

- **Language/Version**: Python 3.14 (floor 3.12)
- **Primary Dependencies**: scion-sdk, fastmcp
- **Storage**: N/A; the connector stores nothing
- **Testing**: pytest; the proof level each row names
- **Target Platform**: Linux containers
- **Project Type**: connector (MCP server)
- **Performance Goals**: N/A
- **Constraints**: one tool per API operation; shared capabilities come from the SDK
- **Scale/Scope**: 2 rows

## Constitution Check

- One owner per concept: pass. The connector owns one external system's calls, mappings and tools only.
- Connectors depend on the SDK and are called through arbora: pass.
- No ratchets: pass. The rows add no suppression.

## Project Structure

```text
pyproject.toml  existing
```

## Phase 0: Research

No unknowns. Each row names the code it touches.

## Phase 1: Design

The rows are delivered in place; the design is the caller chain below.

## Phase 2: Task approach

`tasks.md` holds one task line per row, producer first.

## Complexity Tracking

None. The constitution check passed.

## Build contract

The repository pre-commit hooks apply: `ruff-format`, `connector-standard`, `secrets`, `tests-fast`. Each row names its proving test. No suppression and no duplicate implementation.

## Production caller chain

1. `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R001`: the erpnext-mcp console script (scion_sdk.cli:serve) loads the scion_sdk.connector entry point erpnext_agent:connector (erpnext_agent/__init__.py:89), and the SDK build_server serves the packaged skills, ontology and prompts as resources and prompts.
2. `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R002`: (planned) the connector manifest generator in the pipelines repo (pipelines_hooks/connector/generate.py) reads erpnext_agent/connector_sources.py and the ontology, and writes connector_manifest.yml at the repo root, which does not exist yet; the manifest is consumed by the connector manifest gate.

## Cross-repo seams

none. The cited owner rows are library capabilities the connector calls in process; spec.md names them.
