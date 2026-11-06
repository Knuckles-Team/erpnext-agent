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
4. **Given** the connector is configured, **When** the behaviour of row `CONN-ERPNEXT-AGENT-R008` (every HR operation is its own typed tool) is exercised, **Then** `tests/test_hr_operations.py::test_employee_master_hire_update_list_and_relieve`.
5. **Given** the connector is configured, **When** the behaviour of row `CONN-ERPNEXT-AGENT-R009` (every CRM operation is its own typed tool) is exercised, **Then** `tests/test_crm_operations.py::test_lead_capture_update_qualify_and_list`.
6. **Given** the connector is configured, **When** the behaviour of row `CONN-ERPNEXT-AGENT-R010` (business onboarding is validated, dry-run first, idempotent and verified) is exercised, **Then** `tests/test_business_onboarding.py::test_plan_validates_inputs_against_the_server`.

### Edge Cases

- If `CONN-ERPNEXT-AGENT-R001` is not met, its proving test fails: connector reports its released version.
- If `CONN-ERPNEXT-AGENT-R002` is not met, its proving test fails: supplier and purchase-order access fields match served tool data.
- If `CONN-ERPNEXT-AGENT-R003` is not met, its proving test fails: supplier table recorded response.
- If `CONN-ERPNEXT-AGENT-R008` is not met, its proving test fails: every HR operation is its own typed tool.
- If `CONN-ERPNEXT-AGENT-R009` is not met, its proving test fails: every CRM operation is its own typed tool.
- If `CONN-ERPNEXT-AGENT-R010` is not met, its proving test fails: business onboarding is validated, dry-run first, idempotent and verified.

## Requirements

- **FR-001**: Connector reports its released version. Rows: `CONN-ERPNEXT-AGENT-R001`.
- **FR-002**: Supplier and purchase-order access fields match served tool data. Rows: `CONN-ERPNEXT-AGENT-R002`.
- **FR-003**: Supplier table recorded response. Rows: `CONN-ERPNEXT-AGENT-R003`.
- **FR-004**: Supplier and purchase-order contract fields and recorded fixture. Rows: `CONN-ERPNEXT-AGENT-R004`.
- **FR-005**: Every Frappe business operation is its own typed tool. Rows: `CONN-ERPNEXT-AGENT-R005`.
- **FR-006**: A refused call returns the server's reason. Rows: `CONN-ERPNEXT-AGENT-R006`.
- **FR-007**: Every access contract names a served tool and only its parameters. Rows: `CONN-ERPNEXT-AGENT-R007`.
- **FR-008**: Every HR operation is its own typed tool. Rows: `CONN-ERPNEXT-AGENT-R008`.
- **FR-009**: Every CRM operation is its own typed tool. Rows: `CONN-ERPNEXT-AGENT-R009`.
- **FR-010**: Business onboarding is validated, dry-run first, idempotent and verified. Rows: `CONN-ERPNEXT-AGENT-R010`.
- **FR-011**: Document lifecycle is one explicit state machine. Rows: `CONN-ERPNEXT-AGENT-R011`, `CONN-ERPNEXT-AGENT-R011.1`, `CONN-ERPNEXT-AGENT-R011.2`, `CONN-ERPNEXT-AGENT-R011.3`, `CONN-ERPNEXT-AGENT-R011.4`, `CONN-ERPNEXT-AGENT-R011.5`, `CONN-ERPNEXT-AGENT-R011.6`.

## Success Criteria

- **SC-001**: `tests/test_version.py::test_reported_version_matches_the_released_package`. Rows: `CONN-ERPNEXT-AGENT-R001`.
- **SC-002**: `tests/test_access_contracts.py::test_served_access_contracts_match_synthetic_provider`. Rows: `CONN-ERPNEXT-AGENT-R002`.
- **SC-003**: `tests/test_access_contracts.py` reads the recorded response through the declared contract and compares the rows. Rows: `CONN-ERPNEXT-AGENT-R003`.
- **SC-004**: Supplier and purchase-order contract fields and recorded fixture. Rows: `CONN-ERPNEXT-AGENT-R004`.
- **SC-008**: `tests/test_hr_operations.py::test_employee_master_hire_update_list_and_relieve` and the other bound tests of the row pass. Rows: `CONN-ERPNEXT-AGENT-R008`.
- **SC-009**: `tests/test_crm_operations.py::test_lead_capture_update_qualify_and_list` and the other bound tests of the row pass. Rows: `CONN-ERPNEXT-AGENT-R009`.
- **SC-010**: `tests/test_business_onboarding.py::test_plan_validates_inputs_against_the_server` and the other bound tests of the row pass. Rows: `CONN-ERPNEXT-AGENT-R010`.

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
| FR-005 | `CONN-ERPNEXT-AGENT-R005` | [plan.md](plan.md) | T-005 | [test-spec.md](test-spec.md) |
| FR-006 | `CONN-ERPNEXT-AGENT-R006` | [plan.md](plan.md) | T-006 | [test-spec.md](test-spec.md) |
| FR-007 | `CONN-ERPNEXT-AGENT-R007` | [plan.md](plan.md) | T-007 | [test-spec.md](test-spec.md) |
| FR-008 | `CONN-ERPNEXT-AGENT-R008` | [plan.md](plan.md) | T-008 | [test-spec.md](test-spec.md) |
| FR-009 | `CONN-ERPNEXT-AGENT-R009` | [plan.md](plan.md) | T-009 | [test-spec.md](test-spec.md) |
| FR-010 | `CONN-ERPNEXT-AGENT-R010` | [plan.md](plan.md) | T-010 | [test-spec.md](test-spec.md) |
| FR-011 | `CONN-ERPNEXT-AGENT-R011`, `CONN-ERPNEXT-AGENT-R011.1`, `CONN-ERPNEXT-AGENT-R011.2`, `CONN-ERPNEXT-AGENT-R011.3`, `CONN-ERPNEXT-AGENT-R011.4`, `CONN-ERPNEXT-AGENT-R011.5`, `CONN-ERPNEXT-AGENT-R011.6` | [plan.md](plan.md) | T-011 | [test-spec.md](test-spec.md) |
