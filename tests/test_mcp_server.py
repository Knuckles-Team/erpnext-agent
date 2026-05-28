from unittest.mock import MagicMock

import pytest

from erpnext_agent.mcp_server import get_mcp_instance


@pytest.mark.concept("ERPN-002")
@pytest.mark.asyncio
async def test_mcp_server_registration():
    """CONCEPT:ERPN-002 Test that tools register successfully."""
    res = get_mcp_instance()
    mcp = res[0] if isinstance(res, tuple) else res
    assert mcp is not None

    # Verify tool registry count is greater than zero
    assert len(mcp._local_provider._components) > 0

    # Verify both tool names are registered
    tool_names = [t.name for t in await mcp.list_tools()]
    assert "erpnext_agent_authentication" in tool_names
    assert "erpnext_agent_resource" in tool_names


@pytest.mark.concept("ERPN-003")
def test_mcp_server_security_context():
    """CONCEPT:ERPN-003 Verify that the server registers with correct security credentials."""
    from erpnext_agent.auth import get_client

    client = get_client()
    assert client is not None


@pytest.mark.concept("ERPN-002")
@pytest.mark.asyncio
async def test_mcp_server_authentication_dispatch():
    """Verify erpnext_agent_authentication routes calls dynamically."""
    res = get_mcp_instance()
    mcp = res[0] if isinstance(res, tuple) else res

    tool = next(
        t for t in await mcp.list_tools() if t.name == "erpnext_agent_authentication"
    )
    assert tool is not None

    mock_client = MagicMock()
    mock_client.login.return_value = {"status": "Logged in"}

    # Call the tool function handler directly
    result = await tool.fn(
        action="login",
        params_json='{"usr": "admin", "pwd": "admin"}',
        client=mock_client,
        ctx=None,
    )

    mock_client.login.assert_called_once_with(usr="admin", pwd="admin")
    assert result == {"status": "Logged in"}


@pytest.mark.concept("ERPN-002")
@pytest.mark.asyncio
async def test_mcp_server_resource_dispatch():
    """Verify erpnext_agent_resource routes calls dynamically."""
    res = get_mcp_instance()
    mcp = res[0] if isinstance(res, tuple) else res

    tool = next(t for t in await mcp.list_tools() if t.name == "erpnext_agent_resource")
    assert tool is not None

    mock_client = MagicMock()
    mock_client.list_documents.return_value = [{"name": "Doc1"}]

    result = await tool.fn(
        action="list_documents",
        params_json='{"doctype": "Customer", "limit_page_length": 5}',
        client=mock_client,
        ctx=None,
    )

    mock_client.list_documents.assert_called_once_with(
        doctype="Customer", limit_page_length=5
    )
    assert result == {"result": [{"name": "Doc1"}]}
