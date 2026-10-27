"""PIPE-CONNSPEC-R119.4: the ERPNext development skill is packaged."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "erpnext_agent" / "skills" / "erpnext-agent-development" / "SKILL.md"

pytestmark = pytest.mark.spec("PIPE-CONNSPEC-R119.4")


def test_development_skill_has_rapid_contract_and_package_binding() -> None:
    text = SKILL.read_text(encoding="utf-8")
    frontmatter = text.split("---", 2)[1]
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert SKILL.is_file()
    assert re.search(r"^name:\s*erpnext-agent-development\s*$", frontmatter, re.M)
    assert re.search(r"^skill_type:\s*skill\s*$", frontmatter, re.M)
    assert "## Rapid delivery: the 5-minute contract" in text
    for term in (
        "erpnext_agent/__init__.py",
        "erpnext_agent/api_client.py",
        "erpnext_agent/api/api_client_resource.py",
        "erpnext_agent/api/api_client_base.py",
        "erpnext_agent/auth.py",
        "erpnext_agent/mcp_server.py",
        "erpnext_agent/mcp/mcp_authentication.py",
        "erpnext_agent/mcp/mcp_resource.py",
        "erpnext_agent/mcp/mcp_ingest.py",
        "erpnext_agent/connector_sources.py",
        "erpnext_agent/kg_ingest.py",
        "ERPNEXT_URL",
        "ERPNEXT_TOKEN",
        "ERPNEXT_AGENT_USERNAME",
        "ERPNEXT_AGENT_PASSWORD",
        "erpnext-mcp",
        "mcp_config.json",
        "skills/**",
        "python_pipeline.yml@main",
        "container_pipeline.yml@main",
        "render_connector: true",
        "pages_pipeline.yml@main",
        "uv run --locked --extra test pytest",
    ):
        assert term in text

    assert "verify=False" not in text
    assert "--no-verify" not in text
    package_data = project["tool"]["setuptools"]["package-data"]["erpnext_agent"]
    assert "skills/**" in package_data
    assert project["project"]["entry-points"]["agent_connector_sdk.connector"] == {
        "erpnext-mcp": "erpnext_agent:connector"
    }
