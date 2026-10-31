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
