"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``ingest_entities`` / ``ingest_doctype`` seam with a fake engine
client (no engine required), asserting the txn add_node/commit + edge calls and the
Frappe DocType → typed-node mappings. CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from typing import Any

import msgpack
import pytest
from agent_utilities.knowledge_graph.memory.native_ingest import NativeIngestError
from agent_utilities.security.brain_context import ActorContext, use_actor
from agent_utilities.models.company_brain import ActorType
from agent_utilities.knowledge_graph.core.session import GraphSession, use_session

from erpnext_agent.kg_ingest import ingest_doctype, ingest_entities


@pytest.fixture(autouse=True)
def _governed_session():
    actor = ActorContext(
        actor_id="subject:opaque:synthetic",
        actor_type=ActorType.AUTOMATED_SERVICE,
        roles=(),
        tenant_id="tenant:opaque:synthetic",
        authenticated=True,
    )
    session = GraphSession(
        actor=actor,
        tenant=actor.tenant_id,
        scopes=frozenset({"kg:write"}),
        graph="graph:opaque:synthetic",
        policy_version="policy:opaque:synthetic",
        audience="epistemic-graph",
    )
    with use_actor(actor), use_session(session):
        yield


class _FakeNodes:
    def __init__(self) -> None:
        self.values: dict[str, dict[str, Any]] = {}

    def properties(self, node_id: str) -> dict[str, Any] | None:
        return self.values.get(node_id)

    def list(self) -> list[tuple[str, dict[str, Any]]]:
        return list(self.values.items())


class _FakeChanges:
    def __init__(self, nodes: _FakeNodes) -> None:
        self.nodes = nodes
        self.edges: list[tuple[str, str, dict[str, Any]]] = []
        self.applied: list[dict[str, Any]] = []
        self.records: dict[str, dict[str, Any]] = {}
        self.versions: dict[str, dict[str, Any]] = {}

    def get(self, envelope_id: str) -> dict[str, Any] | None:
        return self.records.get(envelope_id)

    def content_version(self, object_id: str) -> dict[str, Any] | None:
        return self.versions.get(object_id)

    def cursor(self, _source: str, _partition: str = "") -> None:
        return None

    def apply(self, envelope: dict[str, Any]) -> dict[str, Any]:
        self.applied.append(envelope)
        mutation = envelope["mutation"]
        for operation in mutation["operations"]:
            method = operation["method"]
            params = method["params"]
            properties = msgpack.unpackb(params["properties_msgpack"], raw=False)
            if method["method"] == "AddNode":
                self.nodes.values[params["node_id"]] = properties
            elif method["method"] == "AddEdge":
                self.edges.append(
                    (params["source_id"], params["target_id"], properties)
                )
        version = envelope["content_version"]
        self.versions[version["object_id"]] = version
        self.records[envelope["envelope_id"]] = envelope
        return {
            "batch_id": mutation["batch_id"],
            "replayed": False,
            "projection_pending": False,
        }


class _FakeRdf:
    def validate_shacl(self, _shapes: str, _data_graph: str) -> dict[str, Any]:
        return {"conforms": True, "results": []}


class _FakeClient:
    def __init__(self) -> None:
        self.nodes = _FakeNodes()
        self.changes = _FakeChanges(self.nodes)
        self.rdf = _FakeRdf()

    @staticmethod
    def supports(operation: str) -> bool:
        return operation == "ApplyChangeEnvelope"


def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
        [
            {"id": "erpnext:customer:acme", "node_type": "Customer", "name": "Acme"},
            {"id": "erpnext:salesorder:SO-1", "node_type": "SalesOrder"},
        ],
        [
            {
                "source": "erpnext:salesorder:SO-1",
                "target": "erpnext:customer:acme",
                "relationship": "orderedBy",
            }
        ],
        client=c,
    )
    assert res == {"nodes": 2, "edges": 1}
    assert len(c.changes.applied) == 1
    # provenance is stamped by the shared primitive
    assert c.nodes.values["erpnext:customer:acme"]["source"] == "erpnext-agent"
    assert c.nodes.values["erpnext:customer:acme"]["domain"] == "erpnext"
    assert c.changes.edges == [
        (
            "erpnext:salesorder:SO-1",
            "erpnext:customer:acme",
            {"relationship": "orderedBy"},
        )
    ]


def test_ingest_sales_order_maps_customer_and_items():
    c = _FakeClient()
    res = ingest_doctype(
        "Sales Order",
        [
            {
                "name": "SO-2026-0001",
                "customer": "Acme Corp",
                "grand_total": 1250.5,
                "docstatus": 1,
                "transaction_date": "2026-07-04",
                "items": [
                    {"item_code": "WIDGET-1", "item_name": "Widget", "uom": "Nos"},
                    {"item_code": "WIDGET-2"},
                ],
            }
        ],
        client=c,
    )
    # SalesOrder + Customer + 2 Items = 4 nodes; orderedBy + 2 contains = 3 edges
    assert res == {"nodes": 4, "edges": 3}
    so = c.nodes.values["erpnext:salesorder:SO-2026-0001"]
    assert so["node_type"] == "SalesOrder"
    assert so["grandTotal"] == 1250.5
    assert so["docStatus"] == 1
    assert so["postingDate"] == "2026-07-04"
    assert c.nodes.values["erpnext:customer:Acme_Corp"]["node_type"] == "Customer"
    assert c.nodes.values["erpnext:item:WIDGET-1"]["node_type"] == "Item"
    assert (
        "erpnext:salesorder:SO-2026-0001",
        "erpnext:customer:Acme_Corp",
        {"relationship": "orderedBy"},
    ) in c.changes.edges
    assert (
        "erpnext:salesorder:SO-2026-0001",
        "erpnext:item:WIDGET-1",
        {"relationship": "contains"},
    ) in c.changes.edges


def test_ingest_purchase_order_maps_supplier():
    c = _FakeClient()
    res = ingest_doctype(
        "Purchase Order",
        [{"name": "PO-1", "supplier": "Globex", "grand_total": 42.0, "docstatus": 0}],
        client=c,
    )
    assert res == {"nodes": 2, "edges": 1}
    assert c.nodes.values["erpnext:purchaseorder:PO-1"]["node_type"] == "PurchaseOrder"
    assert c.nodes.values["erpnext:supplier:Globex"]["node_type"] == "Supplier"
    assert c.changes.edges == [
        (
            "erpnext:purchaseorder:PO-1",
            "erpnext:supplier:Globex",
            {"relationship": "suppliedBy"},
        )
    ]


def test_ingest_employee_maps_department_link():
    c = _FakeClient()
    res = ingest_doctype(
        "Employee",
        [{"name": "HR-EMP-1", "employee_name": "Jane Doe", "department": "Sales"}],
        client=c,
    )
    assert res == {"nodes": 2, "edges": 1}
    assert c.nodes.values["erpnext:employee:HR-EMP-1"]["node_type"] == "Employee"
    assert c.nodes.values["erpnext:employee:HR-EMP-1"]["employeeName"] == "Jane Doe"
    assert c.nodes.values["erpnext:orgunit:Sales"]["node_type"] == "OrgUnit"
    assert c.changes.edges == [
        (
            "erpnext:employee:HR-EMP-1",
            "erpnext:orgunit:Sales",
            {"relationship": "memberOf"},
        )
    ]


def test_ingest_item_catalog():
    c = _FakeClient()
    res = ingest_doctype(
        "Item",
        [
            {
                "name": "WIDGET-1",
                "item_code": "WIDGET-1",
                "item_name": "Widget",
                "item_group": "Products",
            }
        ],
        client=c,
    )
    assert res == {"nodes": 1, "edges": 0}
    assert c.nodes.values["erpnext:item:WIDGET-1"]["node_type"] == "Item"
    assert c.nodes.values["erpnext:item:WIDGET-1"]["item_group"] == "Products"


def test_unsupported_doctype_is_rejected():
    with pytest.raises(NativeIngestError, match="unsupported ERPNext document type"):
        ingest_doctype(
            "Journal Entry",
            [{"name": "JV-1"}],
            client=_FakeClient(),
        )


def test_retired_node_type_alias_is_rejected():
    with pytest.raises(NativeIngestError, match="canonical node_type"):
        ingest_entities(
            [{"id": "retired", "type": "RetiredAlias"}],
            client=_FakeClient(),
        )


def test_empty_native_ingest_is_rejected():
    with pytest.raises(NativeIngestError, match="at least one entity"):
        ingest_entities([], client=_FakeClient())
