"""The ontology describes the served surface, rolls up to core and locates the data."""

import asyncio
from pathlib import Path

import pytest
from fastmcp import Client
from scion_sdk.testing.ontology_rollup import (
    CORE_NAMESPACE,
    orphan_classes,
    parse_triples,
)

ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY = ROOT / "erpnext_agent" / "ontology"
SKILLS = ROOT / "erpnext_agent" / "skills"
PROMPTS = ROOT / "erpnext_agent" / "prompts"
RDF_TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
SUBCLASS = "http://www.w3.org/2000/01/rdf-schema#subClassOf"
CP = "https://knuckles-team.github.io/ontology/connector-pack#"
VG = "https://knuckles-team.github.io/ontology/virtual-graph#"
OWL_CLASS = "http://www.w3.org/2002/07/owl#Class"
OWL_IMPORTS = "http://www.w3.org/2002/07/owl#imports"


def _triples(name: str) -> list[tuple[str, str, str]]:
    return parse_triples((ONTOLOGY / name).read_text(encoding="utf-8"))


def _labels(triples, cls: str) -> set[str]:
    """Subjects typed ``cls``."""
    return {s for s, p, o in triples if p == RDF_TYPE and o == cls}


def _served_tools(monkeypatch) -> set[str]:
    from scion_sdk.connector import build_server

    monkeypatch.setenv("ERPNEXT_URL", "https://service.invalid")
    monkeypatch.setenv("AUTH_TYPE", "none")
    _, mcp = build_server("erpnext_agent", command_args=["--transport", "stdio"])

    async def names():
        async with Client(mcp) as client:
            return {tool.name for tool in await client.list_tools()}

    return asyncio.run(names())


@pytest.mark.spec("CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R005")
def test_every_class_rolls_up_to_core_by_subclassing_never_import():
    for path in ONTOLOGY.glob("*.ttl"):
        assert orphan_classes(path) == set(), path.name
        assert not [t for t in parse_triples(path.read_text()) if t[1] == OWL_IMPORTS]
    triples = _triples("erpnext.ttl")
    core_reused = {
        "Customer",
        "Supplier",
        "Company",
        "Employee",
        "PurchaseOrder",
        "PurchaseInvoice",
        "Opportunity",
        "ErpNextIssue",
    }
    supers = {}
    for s, p, o in triples:
        if p == SUBCLASS:
            supers.setdefault(s, set()).add(o)
    for s, p, o in triples:
        if p == RDF_TYPE and o == OWL_CLASS:
            local = s.rsplit("#", 1)[-1]
            if local in core_reused:
                continue
            todo, seen, reached = [s], set(), False
            while todo and not reached:
                cur = todo.pop()
                if cur in seen:
                    continue
                seen.add(cur)
                for u in supers.get(cur, ()):
                    reached = reached or u.startswith(CORE_NAMESPACE)
                    todo.append(u)
            assert reached, local


@pytest.mark.spec("CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R006")
def test_surface_lists_exactly_the_served_tools_skills_and_prompts(monkeypatch):
    triples = _triples("surface.ttl")
    # parse_triples drops literals, so names come from the node IRIs.
    tool_names = {s.split("#tool-")[1] for s in _labels(triples, CP + "Tool")}
    skill_names = {s.split("#skill-")[1] for s in _labels(triples, CP + "Skill")}
    prompt_names = {s.split("#prompt-")[1] for s in _labels(triples, CP + "Prompt")}
    assert tool_names and skill_names and prompt_names
    assert tool_names == _served_tools(monkeypatch)
    assert skill_names == {
        p.name for p in SKILLS.iterdir() if (p / "SKILL.md").is_file()
    }
    assert prompt_names == {p.stem for p in PROMPTS.glob("*.json")}
    features = _labels(triples, CP + "Feature")
    realized = {s for s, p, o in triples if p == CP + "realizedBy"}
    assert features and features <= realized
    for tool in _labels(triples, CP + "Tool"):
        assert any(s == tool and p == CP + "operatesOn" for s, p, o in triples), tool
    used_skills = {
        o for s, p, o in triples if p == CP + "realizedBy" and "#skill-" in o
    }
    workflow = {s for s in _labels(triples, CP + "Skill") if "development" not in s}
    assert workflow <= used_skills


@pytest.mark.spec("CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R007")
def test_every_domain_class_has_a_live_virtual_authority():
    classes = {
        s for s, p, o in _triples("erpnext.ttl") if p == RDF_TYPE and o == OWL_CLASS
    }
    fed = _triples("federation.ttl")
    authorities = _labels(fed, VG + "SourceAuthority")
    served = {o for s, p, o in fed if p == VG + "authorityFor" and s in authorities}
    # Abstract parents (Invoice) and computed outputs (ErpReport) have no own records.
    assert classes - served == {
        "https://knuckles-team.github.io/ontology/connector/erpnext#Invoice",
        "https://knuckles-team.github.io/ontology/connector/erpnext#ErpReport",
    }
    for authority in authorities:
        mapping = {
            o for s, p, o in fed if s == authority and p == VG + "authorityMapping"
        }
        assert len(mapping) == 1, authority
        assert any(s in mapping and p == VG + "mapsOntologyClass" for s, p, o in fed)
    sources = _labels(fed, VG + "SourceConnection")
    assert len(sources) == 1
