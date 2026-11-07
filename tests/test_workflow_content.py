"""Workflow skills and the operator prompt name only served tools and shipped skills."""

import asyncio
import json
import re
from pathlib import Path

import pytest
from fastmcp import Client

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "erpnext_agent" / "skills"
PROMPTS = ROOT / "erpnext_agent" / "prompts"
PROMPT = PROMPTS / "erp_operator.json"
WORKFLOWS = {
    "erpnext-order-to-cash",
    "erpnext-procure-to-pay",
    "erpnext-inventory",
    "erpnext-crm-pipeline",
    "erpnext-lead-nurturing",
    "erpnext-projects",
    "erpnext-hr",
    "erpnext-hire-to-retire",
    "erpnext-leave-approval",
    "erpnext-payroll-run",
    "erpnext-accounting",
    "erpnext-business-onboarding",
}
ROLE_PROMPTS = {
    "hr_manager": {
        "erpnext-hr",
        "erpnext-hire-to-retire",
        "erpnext-leave-approval",
        "erpnext-payroll-run",
    },
    "sales_rep": {
        "erpnext-lead-nurturing",
        "erpnext-crm-pipeline",
        "erpnext-order-to-cash",
    },
    "business_onboarding": {
        "erpnext-business-onboarding",
        "erpnext-hr",
        "erpnext-crm-pipeline",
        "erpnext-accounting",
    },
}
AGENT_SECTIONS = (
    "Goal:",
    "Skills",
    "Tools you use:",
    "Data you read:",
    "Data you write:",
    "Guardrails:",
    "Expected outputs:",
)
TOOL_TOKEN = re.compile(r"`(erpnext_(?!agent`)[a-z_]+)`")


def _served(monkeypatch) -> tuple[set[str], set[str]]:
    from scion_sdk.connector import build_server

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


@pytest.mark.spec("CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R008")
def test_role_prompts_are_complete_agent_definitions(monkeypatch):
    tools, _ = _served(monkeypatch)
    for name, skills in {"erp_operator": WORKFLOWS, **ROLE_PROMPTS}.items():
        prompt = json.loads((PROMPTS / f"{name}.json").read_text(encoding="utf-8"))
        directive = prompt["instructions"]["core_directive"]
        for section in AGENT_SECTIONS:
            assert section in directive, (name, section)
        assert set(prompt["skills"]) == skills, name
        assert set(prompt["tools"]) <= tools, (name, set(prompt["tools"]) - tools)
        for tool in prompt["tools"]:
            assert tool in directive, (name, tool)
        for skill in prompt["skills"]:
            assert (SKILLS / skill / "SKILL.md").is_file(), (name, skill)
            assert skill in directive, (name, skill)
        assert prompt["instructions"]["guardrails"], name


@pytest.mark.spec("CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R003")
def test_onboarding_skill_ships_its_input_schema():
    import yaml

    spec = yaml.safe_load(
        (
            SKILLS
            / "erpnext-business-onboarding"
            / "references"
            / "onboarding-spec.yaml"
        ).read_text(encoding="utf-8")
    )
    for key in ("name", "abbr", "country", "currency", "chart_of_accounts"):
        assert key in spec["company"], key
    assert {"start_date", "end_date"} <= set(spec["fiscal_year"])
    assert spec["mode"] in ("auto", "setup_wizard", "company")
    assert {"time_zone", "address", "bank", "hr", "crm"} <= set(spec)


@pytest.mark.spec("CONNECTOR-CONTENT-R009.3")
def test_lifecycle_guidance_names_amend_and_every_refusal_reason():
    from erpnext_agent.lifecycle import RefusalReason

    texts = [
        (SKILLS / f"erpnext-{k}" / "SKILL.md").read_text(encoding="utf-8")
        for k in ("order-to-cash", "procure-to-pay", "accounting")
    ]
    texts.append(PROMPT.read_text(encoding="utf-8"))
    for text in texts:
        assert "erpnext_amend_document" in text
        for reason in RefusalReason:
            assert reason.value in text, reason
