"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``ingest_entities`` / ``ingest_doctype`` seam with a fake engine
client (no engine required), asserting the txn add_node/commit + edge calls and the
Frappe DocType → typed-node mappings. CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from erpnext_agent.kg_ingest import ingest_doctype, ingest_entities


class _FakeTxn:
    def __init__(self):
        self.nodes = {}
        self.committed = False

    def begin(self, graph=None):
        self.graph = graph
        return "txn-1"

    def add_node(self, txn, node_id, props):
        self.nodes[node_id] = props

    def commit(self, txn):
        self.committed = True
        return True


class _FakeEdges:
    def __init__(self):
        self.edges = []

    def add(self, src, dst, props):
        self.edges.append((src, dst, props))


class _FakeClient:
    def __init__(self):
        self.txn = _FakeTxn()
        self.edges = _FakeEdges()


def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
        [
            {"id": "erpnext:customer:acme", "type": "Customer", "name": "Acme"},
            {"id": "erpnext:salesorder:SO-1", "type": "SalesOrder"},
        ],
        [{"source": "erpnext:salesorder:SO-1", "target": "erpnext:customer:acme", "type": "orderedBy"}],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 2, "edges": 1}
    assert c.txn.committed is True
    # provenance is stamped by the shared primitive
    assert c.txn.nodes["erpnext:customer:acme"]["source"] == "erpnext-agent"
    assert c.txn.nodes["erpnext:customer:acme"]["domain"] == "erpnext"
    assert c.edges.edges == [
        ("erpnext:salesorder:SO-1", "erpnext:customer:acme", {"type": "orderedBy"})
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
    assert so["type"] == "SalesOrder"
    assert so["grandTotal"] == 1250.5
    assert so["docStatus"] == 1
    assert so["postingDate"] == "2026-07-04"
    assert c.txn.nodes["erpnext:customer:Acme_Corp"]["type"] == "Customer"
    assert c.txn.nodes["erpnext:item:WIDGET-1"]["type"] == "Item"
    assert (
        "erpnext:salesorder:SO-2026-0001",
        "erpnext:customer:Acme_Corp",
        {"type": "orderedBy"},
    ) in c.edges.edges
    assert (
        "erpnext:salesorder:SO-2026-0001",
        "erpnext:item:WIDGET-1",
        {"type": "contains"},
    ) in c.edges.edges


def test_ingest_purchase_order_maps_supplier():
    c = _FakeClient()
    res = ingest_doctype(
        "Purchase Order",
        [{"name": "PO-1", "supplier": "Globex", "grand_total": 42.0, "docstatus": 0}],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 2, "edges": 1}
    assert c.txn.nodes["erpnext:purchaseorder:PO-1"]["type"] == "PurchaseOrder"
    assert c.txn.nodes["erpnext:supplier:Globex"]["type"] == "Supplier"
    assert c.edges.edges == [
        ("erpnext:purchaseorder:PO-1", "erpnext:supplier:Globex", {"type": "suppliedBy"})
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
    assert c.txn.nodes["erpnext:employee:HR-EMP-1"]["type"] == "Employee"
    assert c.txn.nodes["erpnext:employee:HR-EMP-1"]["employeeName"] == "Jane Doe"
    assert c.txn.nodes["erpnext:orgunit:Sales"]["type"] == "OrgUnit"
    assert c.edges.edges == [
        ("erpnext:employee:HR-EMP-1", "erpnext:orgunit:Sales", {"type": "memberOf"})
    ]


def test_ingest_item_catalog():
    c = _FakeClient()
    res = ingest_doctype(
        "Item",
        [{"name": "WIDGET-1", "item_code": "WIDGET-1", "item_name": "Widget", "item_group": "Products"}],
        client=c,
    )
    assert res == {"nodes": 1, "edges": 0}
    assert c.txn.nodes["erpnext:item:WIDGET-1"]["type"] == "Item"
    assert c.txn.nodes["erpnext:item:WIDGET-1"]["item_group"] == "Products"


def test_unsupported_doctype_is_noop():
    assert ingest_doctype("Journal Entry", [{"name": "JV-1"}], client=_FakeClient()) is None


def test_ingest_noops_without_engine():
    # No injected client + no reachable engine -> clean no-op.
    assert ingest_entities([{"id": "erpnext:item:x", "type": "Item"}]) is None


def test_ingest_empty_is_noop():
    assert ingest_entities([], client=_FakeClient()) is None
    assert ingest_doctype("Sales Order", [], client=_FakeClient()) is None
