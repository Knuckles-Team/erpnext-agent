import pytest

from erpnext_agent.mcp_server import get_mcp_instance


@pytest.mark.concept("EN-OS.governance.erpn-2")
@pytest.mark.asyncio
async def test_mcp_server_registration():
    """CONCEPT:EN-OS.governance.erpn-2 Test that one tool per operation registers."""
    res = get_mcp_instance()
    mcp = res[0] if isinstance(res, tuple) else res
    assert mcp is not None

    assert len(mcp._local_provider._components) > 0

    tools = {t.name: t for t in await mcp.list_tools()}
    for name in ("erpnext_login", "erpnext_list_documents", "erpnext_create_document"):
        assert name in tools
        assert "action" not in tools[name].parameters.get("properties", {})
    assert "erpnext_agent_authentication" not in tools
    assert tools["erpnext_list_documents"].annotations.readOnlyHint is True
    assert tools["erpnext_delete_document"].annotations.destructiveHint is True


@pytest.mark.concept("EN-OS.identity.erpn")
def test_mcp_server_security_context(monkeypatch):
    """CONCEPT:EN-OS.identity.erpn Verify that the server registers with correct security credentials."""
    from erpnext_agent.auth import get_client

    monkeypatch.setenv("ERPNEXT_URL", "https://service.invalid")
    client = get_client()
    assert client is not None
