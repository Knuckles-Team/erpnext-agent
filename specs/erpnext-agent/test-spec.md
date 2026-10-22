# CONN-ERPNEXT-AGENT — Test specification

| Case | Fixture/action | Expected result |
| --- | --- | --- |
| VER-T1 | Read `erpnext_agent.__version__` and the `pyproject.toml` project version | They are equal |

Proof: `tests/test_version.py::test_reported_version_matches_the_released_package` (`CONN-ERPNEXT-AGENT-R001`).
