# CONN-ERPNEXT-AGENT — Connector identity and release metadata

**Owner:** this repository. **Delivery:** SPECIFIED. **Acceptance:** NOT_AUDITED.

See [`requirements.md`](requirements.md) for the definition of every requirement ID this spec owns and [`status.json`](status.json) for their current delivery and acceptance state.

## Outcome

The version the `erpnext_agent` package reports at runtime (`erpnext_agent.__version__`) is the version that was released, so a deployed digest-only image identifies itself correctly in the fleet ledger and in acceptance runs.

## Requirements

| ID | Requirement | Evidence |
| --- | --- | --- |
| `CONN-ERPNEXT-AGENT-R001` | Connector reports its released version: `__version__` equals the `pyproject.toml` version, and the version bump tool updates both together. | `tests/test_version.py` |

## Boundaries

The connector contract, certification and transport rules belong to scion-sdk. Release publication belongs to the repository pipeline.

## Why a new spec

The specs of this repository were read; none owns this capability. This spec states it for this connector only.

## Scope and interfaces

In scope: the rows of [requirements.md](requirements.md). Out of scope: the SDK modules and the engine, which own the shared capabilities.

## User Scenarios & Testing

### User Story 1 - Connector identity and release metadata (Priority: P1)

The version the `erpnext_agent` package reports at runtime (`erpnext_agent.__version__`) is the version that was released, so a deployed digest-only image identifies itself correctly in the fleet ledger and in acceptance runs.

**Acceptance Scenarios**:

1. **Given** the connector is configured, **When** the behaviour of row `CONN-ERPNEXT-AGENT-R001` (connector reports its released version) is exercised, **Then** `tests/test_version.py::test_reported_version_matches_the_released_package`.
2. **Given** the connector is configured, **When** the behaviour of row `CONN-ERPNEXT-AGENT-R002` (supplier and purchase-order access fields match served tool data) is exercised, **Then** `tests/test_access_contracts.py::test_served_access_contracts_match_synthetic_provider`.
3. **Given** the connector is configured, **When** the behaviour of row `CONN-ERPNEXT-AGENT-R003` (supplier table recorded response) is exercised, **Then** `tests/test_access_contracts.py` reads the recorded response through the declared contract and compares the rows.

### Edge Cases

- If `CONN-ERPNEXT-AGENT-R001` is not met, its proving test fails: connector reports its released version.
- If `CONN-ERPNEXT-AGENT-R002` is not met, its proving test fails: supplier and purchase-order access fields match served tool data.
- If `CONN-ERPNEXT-AGENT-R003` is not met, its proving test fails: supplier table recorded response.

## Requirements

- **FR-001**: Connector reports its released version. Rows: `CONN-ERPNEXT-AGENT-R001`.
- **FR-002**: Supplier and purchase-order access fields match served tool data. Rows: `CONN-ERPNEXT-AGENT-R002`.
- **FR-003**: Supplier table recorded response. Rows: `CONN-ERPNEXT-AGENT-R003`.
- **FR-004**: Supplier and purchase-order contract fields and recorded fixture. Rows: `CONN-ERPNEXT-AGENT-R004`.

## Success Criteria

- **SC-001**: `tests/test_version.py::test_reported_version_matches_the_released_package`. Rows: `CONN-ERPNEXT-AGENT-R001`.
- **SC-002**: `tests/test_access_contracts.py::test_served_access_contracts_match_synthetic_provider`. Rows: `CONN-ERPNEXT-AGENT-R002`.
- **SC-003**: `tests/test_access_contracts.py` reads the recorded response through the declared contract and compares the rows. Rows: `CONN-ERPNEXT-AGENT-R003`.
- **SC-004**: Supplier and purchase-order contract fields and recorded fixture. Rows: `CONN-ERPNEXT-AGENT-R004`.

## Assumptions

- The external system is reachable with operator-supplied credentials.
- The SDK and engine contracts the rows cite are at the floors declared in `pyproject.toml`.

## Traceability

| Label | Rows | Design section | Test ID | Evidence |
|---|---|---|---|---|
| FR-001 | `CONN-ERPNEXT-AGENT-R001` | [plan.md](plan.md) | T-001 | [test-spec.md](test-spec.md) |
| FR-002 | `CONN-ERPNEXT-AGENT-R002` | [plan.md](plan.md) | T-002 | [test-spec.md](test-spec.md) |
| FR-003 | `CONN-ERPNEXT-AGENT-R003` | [plan.md](plan.md) | T-003 | [test-spec.md](test-spec.md) |
| FR-004 | `CONN-ERPNEXT-AGENT-R004` | [plan.md](plan.md) | T-004 | [test-spec.md](test-spec.md) |
