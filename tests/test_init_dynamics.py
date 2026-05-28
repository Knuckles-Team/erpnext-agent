import pytest


@pytest.mark.concept("ERPN-001")
def test_init_dynamics():
    import erpnext_agent

    assert erpnext_agent._MCP_AVAILABLE is True
