"""Main FastMCP server and tool registration.

Every Frappe REST operation is its own typed tool, derived by the SDK from
the public methods of :class:`erpnext_agent.api_client.Api`. Only the native
knowledge-graph ingest tool is registered by hand.
"""

from erpnext_agent.mcp.mcp_ingest import register_ingest_tools

# (tag, env-toggle, registrar) — env names are the framework-derived <TAG>TOOL form.
TOOL_REGISTRY = [
    ("ingest", "INGESTTOOL", register_ingest_tools),
]
