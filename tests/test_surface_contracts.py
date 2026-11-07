"""The surface contracts cover every served tool and every prompt is an agent definition."""

import asyncio
import json
from pathlib import Path

import pytest
from fastmcp import Client

from erpnext_agent import connector_contracts as cc

PROMPTS = Path(__file__).resolve().parents[1] / "erpnext_agent" / "prompts"


def _tools(monkeypatch) -> set[str]:
    from scion_sdk._connector_serve import build_server

    monkeypatch.setenv("ERPNEXT_URL", "https://service.invalid")
    monkeypatch.setenv("AUTH_TYPE", "none")
    _, mcp = build_server("erpnext_agent", command_args=["--transport", "stdio"])

    async def names():
        async with Client(mcp) as client:
            return {t.name for t in await client.list_tools()}

    return asyncio.run(names())


@pytest.mark.spec("CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R010")
def test_every_served_tool_has_a_tool_use_contract_and_a_prompt_link(monkeypatch):
    served = _tools(monkeypatch)
    contracted = {s.tool for c in cc.CONTRACTS for s in c.steps}
    linked = {t for link in cc.LINKS for t in link.tools}
    assert served == contracted
    assert served <= linked
    assert len(served) == 87


@pytest.mark.spec("CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R010")
def test_every_prompt_is_an_agent_definition_and_session_skill_is_linked():
    kinds = {}
    for path in PROMPTS.glob("*.json"):
        agent = json.loads(path.read_text(encoding="utf-8")).get("agent")
        assert agent, path.name
        kinds[path.stem] = agent["kind"]
    assert "operator" in kinds.values()
    assert sorted(kinds.values()).count("business-role") == 4
    session = [link for link in cc.LINKS if "erpnext-session" in link.skills]
    assert {"erpnext_login", "erpnext_logout", "erpnext_get_logged_user"} <= set(
        session[0].tools
    )
    task_names = {c.task for c in cc.CONTRACTS}
    assert all(set(r.tasks) <= task_names for r in cc.ROLES)
