import pytest


@pytest.mark.concept("ERPN-002")
def test_startup():
    # Basic import test
    import erpnext_agent

    assert erpnext_agent.__version__  # value is checked in test_version.py
