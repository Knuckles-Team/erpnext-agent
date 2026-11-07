"""The Frappe document lifecycle machine: legality is decided before any write."""

import asyncio
import re
from itertools import product
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from erpnext_agent import kg_ingest
from erpnext_agent.api_client import Api
from erpnext_agent.lifecycle import (
    TRANSITIONS,
    DocumentEvent,
    DocumentState,
    Guards,
    IllegalTransition,
    RefusalReason,
    state_of,
    transition,
)

S, E = DocumentState, DocumentEvent
LEGAL = {
    "draft-save": (S.Draft, E.Save, S.Draft),
    "draft-submit": (S.Draft, E.Submit, S.Submitted),
    "submitted-cancel": (S.Submitted, E.Cancel, S.Cancelled),
    "cancelled-amend": (S.Cancelled, E.Amend, S.Draft),
}


class FakeFrappe:
    """In-memory transport: answers reads, records every write request."""

    def __init__(self, docs, submittable=True, links=()):
        self.docs = {(d["doctype"], d["name"]): dict(d) for d in docs}
        self.submittable = submittable
        self.links = list(links)
        self.requests: list[tuple[str, str]] = []
        self.posts: list[tuple[str, dict]] = []

    @property
    def writes(self):
        return [r for r in self.requests if r[0] != "GET"]

    def __call__(self, method, endpoint, params=None, data=None, files=None):
        self.requests.append((method, endpoint))
        if method == "GET" and endpoint.startswith("/api/resource/"):
            _, _, _, dt, name = endpoint.split("/")
            dt = dt.replace("%20", " ")
            return {"data": dict(self.docs[(dt, name)])}
        if endpoint.endswith("getdoctype"):
            dt = params["doctype"]
            return {"docs": [{"name": dt, "is_submittable": int(self.submittable)}]}
        if endpoint.endswith("get_submitted_linked_docs"):
            return {"message": {"docs": self.links, "count": len(self.links)}}
        self.posts.append((endpoint, data))
        return {"message": {}}


def _api(monkeypatch, fake):
    api = Api(base_url="http://localhost")
    monkeypatch.setattr(api, "request", fake)
    return api


def _doc(docstatus, doctype="Sales Invoice", name="SINV-1", **extra):
    return {
        "doctype": doctype,
        "name": name,
        "docstatus": docstatus,
        "modified": "2026-11-06 10:00:00",
        **extra,
    }


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.1")
@pytest.mark.parametrize("case", LEGAL)
def test_every_legal_transition_reaches_its_declared_state(case):
    state, event, target = LEGAL[case]
    assert transition(state, event) is target
    assert TRANSITIONS[(state, event)] is target


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.1")
def test_every_other_state_event_pair_is_refused_with_a_typed_error():
    legal = {(s, e) for s, e, _ in LEGAL.values()}
    assert set(TRANSITIONS) == legal
    for state, event in product(S, E):
        if (state, event) in legal:
            continue
        with pytest.raises(IllegalTransition) as err:
            transition(state, event)
        assert err.value.reason in RefusalReason


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.1")
def test_illegal_transition_carries_machine_from_state_and_event():
    with pytest.raises(IllegalTransition) as err:
        transition(S.Submitted, E.Submit, Guards(doctype="Sales Invoice", name="X"))
    e = err.value
    assert (e.machine, e.state, e.event, e.reason) == (
        "DocumentLifecycle",
        S.Submitted,
        E.Submit,
        RefusalReason.NotDraft,
    )
    assert (e.doctype, e.name, e.code) == (
        "Sales Invoice",
        "X",
        "STATE_TRANSITION_REFUSED",
    )


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.1")
def test_unknown_docstatus_value_is_refused():
    assert [state_of(i) for i in (0, 1, 2)] == [S.Draft, S.Submitted, S.Cancelled]
    for bad in (3, -1, "x", True):
        with pytest.raises(IllegalTransition):
            state_of(bad)


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.2")
@pytest.mark.parametrize("docstatus", [1, 2])
def test_submit_of_a_submitted_or_cancelled_document_is_refused_before_any_post(
    monkeypatch, docstatus
):
    fake = FakeFrappe([_doc(docstatus)])
    with pytest.raises(IllegalTransition) as err:
        _api(monkeypatch, fake).submit_document("Sales Invoice", "SINV-1")
    assert err.value.reason is RefusalReason.NotDraft
    assert fake.writes == []


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.2")
def test_submit_of_a_non_submittable_doctype_is_refused_with_not_submittable(
    monkeypatch,
):
    fake = FakeFrappe([_doc(0, "ToDo", "T1")], submittable=False)
    with pytest.raises(IllegalTransition) as err:
        _api(monkeypatch, fake).submit_document("ToDo", "T1")
    assert err.value.reason is RefusalReason.NotSubmittable
    assert fake.writes == []


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.2")
def test_submit_of_a_draft_posts_once(monkeypatch):
    fake = FakeFrappe([_doc(0)])
    _api(monkeypatch, fake).submit_document("Sales Invoice", "SINV-1")
    assert [p[0] for p in fake.posts] == ["/api/method/frappe.client.submit"]
    assert fake.posts[0][1]["doc"]["name"] == "SINV-1"


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.3")
@pytest.mark.parametrize("docstatus", [0, 2])
def test_cancel_of_a_draft_or_cancelled_document_is_refused_before_any_post(
    monkeypatch, docstatus
):
    fake = FakeFrappe([_doc(docstatus)])
    with pytest.raises(IllegalTransition) as err:
        _api(monkeypatch, fake).cancel_document("Sales Invoice", "SINV-1")
    assert err.value.reason is RefusalReason.NotSubmitted
    assert fake.writes == []


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.3")
def test_cancel_with_submitted_links_is_refused_and_lists_them(monkeypatch):
    link = {"doctype": "Payment Entry", "name": "PAY-9", "docstatus": 1}
    fake = FakeFrappe([_doc(1)], links=[link])
    with pytest.raises(IllegalTransition) as err:
        _api(monkeypatch, fake).cancel_document("Sales Invoice", "SINV-1")
    assert err.value.reason is RefusalReason.HasSubmittedLinks
    assert "Payment Entry PAY-9" in str(err.value)
    assert fake.writes == []


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.3")
def test_cancel_with_a_stale_modified_stamp_is_refused(monkeypatch):
    fake = FakeFrappe([_doc(1)])
    with pytest.raises(IllegalTransition) as err:
        _api(monkeypatch, fake).cancel_document(
            "Sales Invoice", "SINV-1", modified="2026-11-05 09:00:00"
        )
    assert err.value.reason is RefusalReason.StaleDocument
    assert fake.writes == []


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.3")
def test_cancel_of_a_submitted_unlinked_document_posts_once(monkeypatch):
    fake = FakeFrappe([_doc(1)])
    _api(monkeypatch, fake).cancel_document(
        "Sales Invoice", "SINV-1", modified="2026-11-06 10:00:00"
    )
    assert fake.posts == [
        (
            "/api/method/frappe.client.cancel",
            {"doctype": "Sales Invoice", "name": "SINV-1"},
        )
    ]


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.4")
@pytest.mark.parametrize("docstatus", [0, 1])
def test_amend_of_a_non_cancelled_document_is_refused_before_any_post(
    monkeypatch, docstatus
):
    fake = FakeFrappe([_doc(docstatus)])
    with pytest.raises(IllegalTransition) as err:
        _api(monkeypatch, fake).amend_document("Sales Invoice", "SINV-1")
    assert err.value.reason is RefusalReason.NotCancelled
    assert fake.writes == []


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.4")
def test_amend_of_a_cancelled_document_creates_a_draft_with_amended_from(monkeypatch):
    items = [{"name": "row1", "parent": "SINV-1", "item_code": "I", "qty": 2}]
    fake = FakeFrappe([_doc(2, customer="C", items=items, creation="x")])
    _api(monkeypatch, fake).amend_document("Sales Invoice", "SINV-1")
    ((endpoint, body),) = fake.posts
    assert endpoint == "/api/resource/Sales%20Invoice"
    assert body["amended_from"] == "SINV-1" and body["customer"] == "C"
    assert not {"name", "docstatus", "modified", "creation"} & body.keys()
    assert body["items"] == [{"item_code": "I", "qty": 2}]


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.5")
def test_ingested_nodes_carry_document_state_not_raw_docstatus():
    for docstatus, expected in ((0, "Draft"), (1, "Submitted"), (2, "Cancelled")):
        rec = {"name": "SO-1", "customer": "C", "docstatus": docstatus}
        nodes, _ = kg_ingest._order(rec, "SalesOrder", "customer", "Customer", "x")
        order = nodes[0]
        assert order["documentState"] == expected
        assert "docStatus" not in order


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.5")
def test_no_module_outside_lifecycle_compares_docstatus_with_an_integer():
    root = Path(__file__).resolve().parents[1] / "erpnext_agent"
    pattern = re.compile(r"docstatus[\"']?\)?\s*(==|!=|<|>|in)\s*[\(\[]?\s*\d")
    pattern2 = re.compile(r"\bint\(\s*[a-z_]*\.?get\(\s*[\"']docstatus")
    for path in root.rglob("*.py"):
        if path.name == "lifecycle.py":
            continue
        text = path.read_text(encoding="utf-8")
        assert not pattern.search(text), path
        assert not pattern2.search(text), path


def _call(monkeypatch, fake, tool, args):
    from scion_sdk._connector_serve import build_server

    monkeypatch.setenv("ERPNEXT_URL", "https://service.invalid")
    monkeypatch.setenv("AUTH_TYPE", "none")
    monkeypatch.setattr(Api, "request", lambda self, *a, **k: fake(*a, **k))
    _, mcp = build_server("erpnext_agent", command_args=["--transport", "stdio"])

    async def run():
        async with Client(mcp) as client:
            return await client.call_tool(tool, args)

    return asyncio.run(run())


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.6")
@pytest.mark.parametrize(
    "tool,docstatus",
    [
        ("erpnext_submit_document", 1),
        ("erpnext_submit_document", 2),
        ("erpnext_cancel_document", 0),
        ("erpnext_cancel_document", 2),
        ("erpnext_amend_document", 0),
        ("erpnext_amend_document", 1),
    ],
)
def test_served_tools_refuse_illegal_moves_with_zero_write_requests(
    monkeypatch, tool, docstatus
):
    fake = FakeFrappe([_doc(docstatus)])
    with pytest.raises((ToolError, Exception)) as err:
        _call(
            monkeypatch,
            fake,
            tool,
            {"doctype": "Sales Invoice", "name": "SINV-1"},
        )
    assert "STATE_TRANSITION_REFUSED" in str(err.value)
    assert fake.writes == []


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R011.6")
def test_served_submit_of_a_draft_reaches_the_server_once(monkeypatch):
    fake = FakeFrappe([_doc(0)])
    _call(
        monkeypatch,
        fake,
        "erpnext_submit_document",
        {"doctype": "Sales Invoice", "name": "SINV-1"},
    )
    assert len(fake.writes) == 1
