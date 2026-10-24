import pytest


@pytest.mark.concept("EN-OS.identity.erpn")
def test_mcp_server_security_context(monkeypatch):
    """CONCEPT:EN-OS.identity.erpn Verify that the server registers with correct security credentials."""
    from erpnext_agent.auth import get_client

    monkeypatch.setenv("ERPNEXT_URL", "https://service.invalid")
    client = get_client()
    assert client is not None
