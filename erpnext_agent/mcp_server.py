"""Main FastMCP server and tool registration."""

from erpnext_agent.mcp.mcp_authentication import register_authentication_tools
from erpnext_agent.mcp.mcp_ingest import register_ingest_tools
from erpnext_agent.mcp.mcp_resource import register_resource_tools

# (tag, env-toggle, registrar) — env names are the framework-derived <TAG>TOOL form.
TOOL_REGISTRY = [
    ("authentication", "AUTHENTICATIONTOOL", register_authentication_tools),
    ("resource", "RESOURCETOOL", register_resource_tools),
    ("ingest", "INGESTTOOL", register_ingest_tools),
]
