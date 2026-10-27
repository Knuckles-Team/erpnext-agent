# CONN-ERPNEXT-AGENT — Test specification

| Case | Fixture/action | Expected result |
| --- | --- | --- |
| VER-T1 | Read `erpnext_agent.__version__` and the `pyproject.toml` project version | They are equal |

Proof: `tests/test_version.py::test_reported_version_matches_the_released_package` (`CONN-ERPNEXT-AGENT-R001`).
# Synthetic access contracts (CONN-ERPNEXT-AGENT-R002)

`tests/test_access_contracts.py::test_served_access_contracts_match_synthetic_provider`
compares the parsed contracts with the served synthetic supplier and purchase-order data.
