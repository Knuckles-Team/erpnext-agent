import warnings
import logging
import os
import sys
from typing import Any
from fastmcp import Context, FastMCP
from fastmcp.utilities.logging import get_logger
from pydantic import Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from agent_utilities.base_utilities import to_boolean
from agent_utilities.mcp_utilities import create_mcp_server
from dotenv import find_dotenv, load_dotenv

from erpnext_agent.mcp.mcp_resource import register_resource_tools

__version__ = "0.15.0"
logger = get_logger(name="erpnext_agent")

def get_mcp_instance() -> tuple[Any, ...]:
    load_dotenv(find_dotenv())
    args, mcp, middlewares = create_mcp_server(
        name="ERPNext Agent MCP",
        version=__version__,
        instructions="ERPNext Agent MCP Server - Managed dynamic operations.",
    )

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        return JSONResponse({"status": "OK"})

    
    DEFAULT_RESOURCETOOL = to_boolean(os.getenv("RESOURCETOOL", "True"))
    if DEFAULT_RESOURCETOOL:
        register_resource_tools(mcp)

    for mw in middlewares:
        mcp.add_middleware(mw)
    return mcp, args, middlewares

def mcp_server() -> None:
    mcp, args, middlewares = get_mcp_instance()
    print(f"ERPNext Agent MCP v{__version__}", file=sys.stderr)
    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")

if __name__ == "__main__":
    mcp_server()
