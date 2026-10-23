"""CONCEPT:EN-OS.governance.erpn Dynamic client facade orchestration and resource mappings."""

#!/usr/bin/env python
from erpnext_agent import __version__  # single source: package __init__
from erpnext_agent.api.api_client_resource import Api as ResourceApi

__all__ = ["Api", "__version__"]


class Api(ResourceApi):
    pass
