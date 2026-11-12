"""The lifecycle ontology equals the code machine."""

from pathlib import Path

import pytest
from scion_sdk.testing.ontology_rollup import parse_triples

from erpnext_agent.lifecycle import (
    TRANSITIONS,
    DocumentEvent,
    DocumentState,
    RefusalReason,
)

K = "https://knuckles-team.github.io/ontology/core#"
CONNECTOR_NS = "https://knuckles-team.github.io/ontology/connector/erpnext#"
SUB = "http://www.w3.org/2000/01/rdf-schema#subClassOf"
TTL = (
    Path(__file__).resolve().parents[1] / "erpnext_agent" / "ontology" / "lifecycle.ttl"
)


def _t():
    return parse_triples(TTL.read_text(encoding="utf-8"))


def _subs(triples, parent):
    return {
        s.removeprefix(CONNECTOR_NS) for s, p, o in triples if p == SUB and o == K + parent
    }


def _val(triples, s, p):
    return {
        o.removeprefix(K)
        for a, b, o in triples
        if a == CONNECTOR_NS + s and b in (K + p, CONNECTOR_NS + p)
    }


@pytest.mark.spec("CONNECTOR-CONTENT-R009.1")
def test_lifecycle_classes_extend_core_state_machine_classes():
    t = _t()
    assert _subs(t, "StateMachine") == {"DocumentLifecycle"}
    assert _subs(t, "DocumentLifecycleState") and _subs(t, "State") == {
        "DocumentLifecycleState"
    }
    assert _subs(t, "Transition") and _subs(t, "TransitionEvent")
    assert _subs(t, "TransitionGuard") == {
        "SubmittableGuard",
        "NoSubmittedLinksGuard",
        "FreshModifiedGuard",
    }
    assert "owl#imports" not in TTL.read_text()


@pytest.mark.spec("CONNECTOR-CONTENT-R009.2")
def test_ontology_states_and_transitions_equal_the_code_machine():
    t = _t()
    assert _subs(t, "DocumentLifecycleState") == {
        f"{s.value}State" for s in DocumentState
    }
    assert _subs(t, "TransitionEvent") == {f"{e.value}Event" for e in DocumentEvent}
    assert _subs(t, "Transition") == {f"{e.value}Transition" for e in DocumentEvent}
    assert _subs(t, "RefusalCode") == {f"{r.value}Refused" for r in RefusalReason}
    for (state, event), target in TRANSITIONS.items():
        name = f"{event.value}Transition"
        assert _val(t, name, "fromState") == {f"{state.value}State"}
        assert _val(t, name, "toState") == {f"{target.value}State"}
        assert _val(t, name, "firedBy") == {f"{event.value}Event"}
