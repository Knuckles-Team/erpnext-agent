"""MCP tools for authentication operations."""

from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from erpnext_agent.auth import get_client


def register_authentication_tools(mcp: FastMCP):
    """Register ERPNext Agent authentication tools."""

    @mcp.tool(tags={"authentication"})
    async def erpnext_agent_authentication(
        action: str = Field(
            description="Action to perform. Must be one of: 'login', 'logout', 'get_logged_user', 'get_version'"
        ),
        params_json: str = Field(
            default="{}", description="JSON string of parameters."
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """Manage ERPNext Agent authentication operations."""
        if ctx:
            await ctx.info(f"Executing authentication operation: {action}...")
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
            return {"error": f"Unknown action '{action}' on Authentication client."}

        try:
            res = method(**kwargs)
            return res if isinstance(res, dict) else {"result": res}
        except Exception as e:
            return {
                "error": f"Failed to execute authentication operation {action}: {e}"
            }
