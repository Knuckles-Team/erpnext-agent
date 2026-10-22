# CONN-ERPNEXT-AGENT — Design and architecture

`erpnext_agent/__init__.py` carries `__version__`. `.bumpversion.cfg` lists that file next to `pyproject.toml` and the Dockerfile pin, so one bump updates all of them. A stale `__version__` is the failure this prevents: the released image identified itself with an old number although the package metadata was correct.
