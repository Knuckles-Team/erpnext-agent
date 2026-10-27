# CONN-ERPNEXT-AGENT — Design and architecture

`erpnext_agent/__init__.py` carries `__version__`. `.bumpversion.cfg` lists that file next to `pyproject.toml` and the Dockerfile pin, so one bump updates all of them. A stale `__version__` is the failure this prevents: the released image identified itself with an old number although the package metadata was correct.

## Access-contract evidence (CONN-ERPNEXT-AGENT-R002)

Exercise the registered resource tool through MCP with a synthetic provider.
Compare each supplier and purchase-order contract field to its returned record.
A production recording and any additional source-specific status mapping remain separate work.
