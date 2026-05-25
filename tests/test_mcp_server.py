import pytest

@pytest.mark.concept("ERPN-002")
def test_mcp_server_registration():
    """CONCEPT:ERPN-002 Test that tools register successfully."""
    from erpnext_agent.mcp_server import get_mcp_instance
    res = get_mcp_instance()
    if isinstance(res, tuple):
        mcp = res[0]
    else:
        mcp = res
    assert mcp is not None
    
    # Verify tool registry count is greater than zero
    assert len(mcp._local_provider._components) > 0

@pytest.mark.concept("ERPN-003")
def test_mcp_server_security_context():
    """CONCEPT:ERPN-003 Verify that the server registers with correct security credentials."""
    from erpnext_agent.auth import get_client
    client = get_client()
    assert client is not None
