# CONN-ERPNEXT-AGENT requirements

Every requirement this specification owns, with the proof that closes it. Delivery state and
public evidence for each ID are recorded in [`status.json`](status.json); this file defines what
each ID means. The design is in [`spec.md`](spec.md) and [`plan.md`](plan.md), the test contract
in [`test-spec.md`](test-spec.md), and the work order in [`tasks.md`](tasks.md).

| ID | Requirement | Verification |
|---|---|---|
| `CONN-ERPNEXT-AGENT-R001` | **Connector reports its released version.** `erpnext_agent.__version__` equals the released `pyproject.toml` version and the bump configuration updates both. | `tests/test_version.py::test_reported_version_matches_the_released_package` |
| `CONN-ERPNEXT-AGENT-R002` | **Supplier and purchase-order access fields match served tool data.** The declared access contracts name the served resource tool and fields. A synthetic provider exercises the tool over MCP and returns each declared field. This proof does not represent a recorded production response. | `tests/test_access_contracts.py::test_served_access_contracts_match_synthetic_provider` |
| `CONN-ERPNEXT-AGENT-R003` | **Supplier table recorded response.** Moved from `EG-CQ-XSRC-R002.7`. A recorded erpnext `list_documents` response for the Supplier doctype is stored as a fixture and the declared supplier access contract reads the same rows from it that the medulla `vg:VirtualMapping` for `kg:Supplier` expects (key `name`, label `supplier_name`). | `tests/test_access_contracts.py` reads the recorded response through the declared contract and compares the rows. |
