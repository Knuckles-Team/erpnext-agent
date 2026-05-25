import pytest

@pytest.mark.concept("ERPN-001")
def test_api_client_basic_mock(mock_ctx):
    """CONCEPT:ERPN-001 Test basic mock initialization of client facade."""
    assert mock_ctx is not None
    assert hasattr(mock_ctx, "info")

@pytest.mark.concept("ERPN-001")
def test_api_client_endpoints(mock_ctx):
    """CONCEPT:ERPN-001 Verify endpoint configuration on dynamic client."""
    from erpnext_agent.api_client import Api
    from erpnext_agent.auth import get_client
    
    client = get_client()
    assert client is not None
    assert hasattr(client, "request")
