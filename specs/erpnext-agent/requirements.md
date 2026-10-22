# CONN-ERPNEXT-AGENT requirements

Every requirement this specification owns, with the proof that closes it. Delivery state and
public evidence for each ID are recorded in [`status.json`](status.json); this file defines what
each ID means. The design is in [`spec.md`](spec.md) and [`plan.md`](plan.md), the test contract
in [`test-spec.md`](test-spec.md), and the work order in [`tasks.md`](tasks.md).

| ID | Requirement | Verification |
|---|---|---|
| `CONN-ERPNEXT-AGENT-R001` | **Connector reports its released version.** `erpnext_agent.__version__` equals the released `pyproject.toml` version and the bump configuration updates both. | `tests/test_version.py::test_reported_version_matches_the_released_package` |
