# CONN-ERPNEXT-AGENT — Design and architecture

`erpnext_agent/__init__.py` carries `__version__`. `.bumpversion.cfg` lists that file next to `pyproject.toml` and the Dockerfile pin, so one bump updates all of them. A stale `__version__` is the failure this prevents: the released image identified itself with an old number although the package metadata was correct.

## Access-contract evidence (CONN-ERPNEXT-AGENT-R002)

Exercise the registered resource tool through MCP with a synthetic provider.
Compare each supplier and purchase-order contract field to its returned record.
A production recording and any additional source-specific status mapping remain separate work.

## Transactional invoice source prerequisite

The optional `scion_erp_guard` Frappe app is installed on the ERPNext site,
not in the MCP connector process. It commits an idempotency reservation before creation. Creation and
reconciliation lock the same claim row. The invoice and applied receipt commit
in the same Frappe POST transaction. A repeated exact claim returns the
committed receipt. A claim collision aborts the transaction; the client
reconciles before any retry. An absent claim is unknown, not proof that no
source effect occurred. The site operator binds each source user to
one tenant and grants the Sales Invoice permissions separately.

This source app is a prerequisite for SCION-SOURCE-INGEST-R006.33 through
R006.37. Local tests do not prove that a deployed site's app, hooks and
transaction isolation satisfy that contract. The connector still needs a
qualified transport, durable EG approval and receipt binding, and a real
ERPNext served test before the full workflow is complete.
