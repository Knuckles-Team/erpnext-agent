"""MCP tools for resource operations."""

from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from erpnext_agent.auth import get_client


def register_resource_tools(mcp: FastMCP):
    """Register ERPNext Agent resource tools.
    CONCEPT:ERPN-001
    """

    @mcp.tool(tags={"resource"})
    async def erpnext_agent_resource(
        action: str = Field(
            description="Action to perform. Must be one of: 'get_document', 'create_document', 'update_document', 'delete_document', 'list_documents', 'call_method'"
        ),
        params_json: str = Field(
            default="{}", description="JSON string of parameters."
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """Manage ERPNext Agent resource operations."""
        if ctx:
            await ctx.info("Executing resource operations...")
        import json

        try:
            kwargs = json.loads(params_json)
        except Exception as e:
            return {"error": f"Invalid params_json: {e}"}

        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        # Dynamic dispatch
        method = getattr(client, action, None)
        if not method:
            alt_action = action.replace("-", "_").replace(" ", "_").lower()
            method = getattr(client, alt_action, None)

        if not method:
            return {"error": f"Unknown action '{action}' on Resource client."}

        try:
            res = method(**kwargs)
            return res if isinstance(res, dict) else {"result": res}
        except Exception as e:
            return {"error": f"Failed to execute resource operation {action}: {e}"}
