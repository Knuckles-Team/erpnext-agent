"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``ingest_entities`` / ``ingest_doctype`` seam with a fake engine
client (no engine required), asserting the txn add_node/commit + edge calls and the
Frappe DocType → typed-node mappings. CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

import pytest
from agent_utilities.knowledge_graph.memory.native_ingest import NativeIngestError

from erpnext_agent.kg_ingest import ingest_doctype, ingest_entities


class _FakeTxn:
    def __init__(self):
        self.nodes = {}
        self.edges = []
        self.committed = False

    def begin(self, graph=None):
        self.graph = graph
        return "txn-1"

    def add_node(self, txn, node_id, props):
        self.nodes[node_id] = props

    def add_edge(self, txn, source, target, props):
        self.edges.append((source, target, props))

    def commit(self, txn):
        self.committed = True
        return True


class _FakeClient:
    def __init__(self):
        self.txn = _FakeTxn()


def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
        [
            {"id": "erpnext:customer:acme", "node_type": "Customer", "name": "Acme"},
            {"id": "erpnext:salesorder:SO-1", "node_type": "SalesOrder"},
        ],
        [{"source": "erpnext:salesorder:SO-1", "target": "erpnext:customer:acme", "relationship": "orderedBy"}],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 2, "edges": 1}
    assert c.txn.committed is True
    # provenance is stamped by the shared primitive
    assert c.txn.nodes["erpnext:customer:acme"]["source"] == "erpnext-agent"
    assert c.txn.nodes["erpnext:customer:acme"]["domain"] == "erpnext"
    assert c.txn.edges == [
        ("erpnext:salesorder:SO-1", "erpnext:customer:acme", {"relationship": "orderedBy"})
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
        graph="__commons__",
    )
    # SalesOrder + Customer + 2 Items = 4 nodes; orderedBy + 2 contains = 3 edges
    assert res == {"nodes": 4, "edges": 3}
    so = c.txn.nodes["erpnext:salesorder:SO-2026-0001"]
    assert so["node_type"] == "SalesOrder"
    assert so["grandTotal"] == 1250.5
    assert so["docStatus"] == 1
    assert so["postingDate"] == "2026-07-04"
    assert c.txn.nodes["erpnext:customer:Acme_Corp"]["node_type"] == "Customer"
    assert c.txn.nodes["erpnext:item:WIDGET-1"]["node_type"] == "Item"
    assert (
        "erpnext:salesorder:SO-2026-0001",
        "erpnext:customer:Acme_Corp",
        {"relationship": "orderedBy"},
    ) in c.txn.edges
    assert (
        "erpnext:salesorder:SO-2026-0001",
        "erpnext:item:WIDGET-1",
        {"relationship": "contains"},
    ) in c.txn.edges


def test_ingest_purchase_order_maps_supplier():
    c = _FakeClient()
    res = ingest_doctype(
        "Purchase Order",
        [{"name": "PO-1", "supplier": "Globex", "grand_total": 42.0, "docstatus": 0}],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 2, "edges": 1}
    assert c.txn.nodes["erpnext:purchaseorder:PO-1"]["node_type"] == "PurchaseOrder"
    assert c.txn.nodes["erpnext:supplier:Globex"]["node_type"] == "Supplier"
    assert c.txn.edges == [
        ("erpnext:purchaseorder:PO-1", "erpnext:supplier:Globex", {"relationship": "suppliedBy"})
    ]


def test_ingest_employee_maps_department_link():
    c = _FakeClient()
    res = ingest_doctype(
        "Employee",
        [{"name": "HR-EMP-1", "employee_name": "Jane Doe", "department": "Sales"}],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 2, "edges": 1}
    assert c.txn.nodes["erpnext:employee:HR-EMP-1"]["node_type"] == "Employee"
    assert c.txn.nodes["erpnext:employee:HR-EMP-1"]["employeeName"] == "Jane Doe"
    assert c.txn.nodes["erpnext:orgunit:Sales"]["node_type"] == "OrgUnit"
    assert c.txn.edges == [
        ("erpnext:employee:HR-EMP-1", "erpnext:orgunit:Sales", {"relationship": "memberOf"})
    ]


def test_ingest_item_catalog():
    c = _FakeClient()
    res = ingest_doctype(
        "Item",
        [{"name": "WIDGET-1", "item_code": "WIDGET-1", "item_name": "Widget", "item_group": "Products"}],
        client=c,
    )
    assert res == {"nodes": 1, "edges": 0}
    assert c.txn.nodes["erpnext:item:WIDGET-1"]["node_type"] == "Item"
    assert c.txn.nodes["erpnext:item:WIDGET-1"]["item_group"] == "Products"


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
