import sys
import pytest

def test_startup():
    # Basic import test
    import erpnext_agent
    assert erpnext_agent.__version__ == "0.15.0"
