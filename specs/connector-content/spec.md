# CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT — The connector serves its packaged content

Owner: erpnext-agent. Cross-repo IDs: `SCION-CONNECTOR-CONTROL-R071`, `SCION-CONNECTOR-CONTROL-R073`.

## Purpose and user stories

The `erpnext-mcp` server serves its packaged skills, prompts and ontology to any client, with no wiring of its own.

## Why a new spec

The specs of this repository were read; none owns this capability. This spec states it for this connector only.

## Scope and interfaces

In scope: the rows of [requirements.md](requirements.md). Out of scope: the SDK modules and the engine, which own the shared capabilities.

## User Scenarios & Testing

### User Story 1 - The connector serves its packaged content (Priority: P1)

The `erpnext-mcp` server serves its packaged skills, prompts and ontology to any client, with no wiring of its own.

**Acceptance Scenarios**:

1. **Given** the connector is configured, **When** the behaviour of row `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R001` (default content) is exercised, **Then** `resources/list` includes `skill://` and `ontology://`; `prompts/list` includes each packaged prompt.
2. **Given** the connector is configured, **When** the behaviour of row `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R002` (resolve the manifest ontology classes for supplier, item, purchase order and customer) is exercised, **Then** resolve the manifest ontology classes for supplier, item, purchase order and customer.

### Edge Cases

- If `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R001` is not met, its proving test fails: default content.
- If `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R002` is not met, its proving test fails: resolve the manifest ontology classes for supplier, item, purchase order and customer.

## Requirements

- **FR-001**: Default content. Rows: `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R001`.
- **FR-002**: Resolve the manifest ontology classes for supplier, item, purchase order and customer. Rows: `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R002`.
- **FR-003**: Proven business workflows ship as served skills. Rows: `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R003`.
- **FR-004**: The operator prompt names the served tools and the workflow skills. Rows: `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R004`.
- **FR-005**: Every ontology class rolls up to medulla core by subclassing. Rows: `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R005`.
- **FR-006**: The ontology records the served surface and its links. Rows: `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R006`.
- **FR-007**: The ontology locates each class's data and how medulla federates it. Rows: `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R007`.

## Success Criteria

- **SC-001**: `resources/list` includes `skill://` and `ontology://`; `prompts/list` includes each packaged prompt. Rows: `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R001`.
- **SC-002**: Resolve the manifest ontology classes for supplier, item, purchase order and customer. Rows: `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R002`.

## Assumptions

- The external system is reachable with operator-supplied credentials.
- The SDK and engine contracts the rows cite are at the floors declared in `pyproject.toml`.

## Traceability

| Label | Rows | Design section | Test ID | Evidence |
|---|---|---|---|---|
| FR-001 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R001` | [plan.md](plan.md) | T-001 | [test-spec.md](test-spec.md) |
| FR-002 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R002` | [plan.md](plan.md) | T-002 | [test-spec.md](test-spec.md) |
| FR-003 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R003` | [plan.md](plan.md) | T-003 | [test-spec.md](test-spec.md) |
| FR-004 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R004` | [plan.md](plan.md) | T-004 | [test-spec.md](test-spec.md) |
| FR-005 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R005` | [plan.md](plan.md) | T-005 | [test-spec.md](test-spec.md) |
| FR-006 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R006` | [plan.md](plan.md) | T-006 | [test-spec.md](test-spec.md) |
| FR-007 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R007` | [plan.md](plan.md) | T-007 | [test-spec.md](test-spec.md) |
