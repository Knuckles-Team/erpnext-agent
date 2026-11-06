"""Workflow skills and the operator prompt name only served tools and shipped skills."""

import asyncio
import json
import re
from pathlib import Path

import pytest
from fastmcp import Client

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "erpnext_agent" / "skills"
PROMPT = ROOT / "erpnext_agent" / "prompts" / "erp_operator.json"
WORKFLOWS = {
    "erpnext-order-to-cash",
    "erpnext-procure-to-pay",
    "erpnext-inventory",
    "erpnext-crm-pipeline",
    "erpnext-projects",
    "erpnext-hr",
    "erpnext-accounting",
}
TOOL_TOKEN = re.compile(r"`(erpnext_(?!agent`)[a-z_]+)`")


def _served(monkeypatch) -> tuple[set[str], set[str]]:
    from scion_sdk._connector_serve import build_server

    monkeypatch.setenv("ERPNEXT_URL", "https://service.invalid")
    monkeypatch.setenv("AUTH_TYPE", "none")
    _, mcp = build_server("erpnext_agent", command_args=["--transport", "stdio"])

    async def read():
        async with Client(mcp) as client:
            tools = {tool.name for tool in await client.list_tools()}
            uris = {str(r.uri) for r in await client.list_resources()}
            return tools, uris

    return asyncio.run(read())


@pytest.mark.spec("CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R003")
def test_workflow_skills_are_served_and_name_only_served_tools(monkeypatch):
    tools, uris = _served(monkeypatch)
    for skill in WORKFLOWS:
        assert f"skill://{skill}/SKILL.md" in uris, skill
        text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
        named = set(TOOL_TOKEN.findall(text))
        assert named, skill
        assert named <= tools, (skill, named - tools)
    for path in SKILLS.rglob("*.md"):
        stale = set(TOOL_TOKEN.findall(path.read_text(encoding="utf-8"))) - tools
        assert not stale, (path.name, stale)


@pytest.mark.spec("CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R004")
def test_operator_prompt_names_served_tools_and_shipped_workflow_skills(monkeypatch):
    tools, _ = _served(monkeypatch)
    prompt = json.loads(PROMPT.read_text(encoding="utf-8"))
    assert set(prompt["tools"]) <= tools
    assert set(prompt["skills"]) == WORKFLOWS
    assert "erpnext_agent_resource" not in PROMPT.read_text(encoding="utf-8")
