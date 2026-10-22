import importlib
import tomllib
from pathlib import Path

import erpnext_agent


def test_reported_version_matches_the_released_package():
    pyproject = tomllib.loads(
        (Path(__file__).parents[1] / "pyproject.toml").read_text()
    )
    assert erpnext_agent.__version__ == pyproject["project"]["version"]


def test_every_module_reports_the_same_version():
    for name in ("api_client", "mcp_server"):
        module = importlib.import_module(f"erpnext_agent.{name}")
        assert module.__version__ == erpnext_agent.__version__, name
