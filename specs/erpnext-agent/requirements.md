# CONN-ERPNEXT-AGENT requirements

Every requirement this specification owns, with the proof that closes it. Delivery state and
public evidence for each ID are recorded in [`status.json`](status.json); this file defines what
each ID means. The design is in [`spec.md`](spec.md) and [`plan.md`](plan.md), the test contract
in [`test-spec.md`](test-spec.md), and the work order in [`tasks.md`](tasks.md).

| ID | Requirement | Verification |
|---|---|---|
| `CONN-ERPNEXT-AGENT-R001` | **Connector reports its released version.** `erpnext_agent.__version__` equals the released `pyproject.toml` version and the bump configuration updates both. | `tests/test_version.py::test_reported_version_matches_the_released_package` |
| `CONN-ERPNEXT-AGENT-R002` | **Supplier and purchase-order access fields match served tool data.** The declared access contracts name the served resource tool and fields. A synthetic provider exercises the tool over MCP and returns each declared field. This proof does not represent a recorded production response. | `tests/test_access_contracts.py::test_served_access_contracts_match_synthetic_provider` |
| `CONN-ERPNEXT-AGENT-R003` | **Supplier and purchase-order contract fields and recorded fixture.** Add `tests/fixtures/supplier_purchase_order.json` and pin the Supplier and PurchaseOrder fields in `erpnext_agent/ontology/access_contracts.ttl`. The served tool `erpnext_agent_resource` returns exactly those fields for the recorded response. Provider of `SCION-CONNECTOR-CONTROL-R037`. | Test: `tests/test_access_contracts.py::test_supplier_and_purchase_order_fields_match_recorded_fixture` (L3) through the served MCP tool against the recorded response. |
