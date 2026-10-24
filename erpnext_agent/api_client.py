"""CONCEPT:EN-OS.governance.erpn Dynamic client facade orchestration and resource mappings."""

#!/usr/bin/env python
from importlib.metadata import version as _v

from erpnext_agent.api.api_client_resource import Api as ResourceApi

__version__ = _v("erpnext-agent")

__all__ = ["Api", "__version__"]


class Api(ResourceApi):
    pass
