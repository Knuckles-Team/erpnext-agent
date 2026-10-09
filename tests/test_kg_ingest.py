"""Epistemic-graph typed-node ingestion -- Wire-First coverage for erpnext-agent.

Exercises the real ``ingest_entities`` / ``ingest_doctype`` seam against a fake
``agent_connector_sdk.ingest`` transport (no engine required). The real SDK request
builder (``agent_connector_sdk.ingest.request.build_request``) still runs, so a
malformed change set is still caught by the SDK's own contract, not re-derived here;
only the final network commit is faked.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from agent_connector_sdk.ingest import IngestError, KnowledgeIngest
from epistemic_graph.generated.source_ingestion import SourceIngestionRequest

from erpnext_agent.kg_ingest import ingest_doctype, ingest_entities


class _FakeTransport:
    """Records every submitted request; no epistemic-graph engine required."""

    def __init__(self) -> None:
        self.requests: list[SourceIngestionRequest] = []

    async def source_status(self, _connector: str, _stream: str) -> Any:
        return SimpleNamespace(accepted_checkpoint=None)

    async def submit(self, request: SourceIngestionRequest) -> Any:
        self.requests.append(request)
        return SimpleNamespace(
            affected_count=len(request.records),
            relationship_count=len(request.relationships),
        )

    async def store_blob(self, _data: bytes) -> str:
        raise AssertionError("this test carries no media")


@pytest.fixture
def ingest() -> tuple[KnowledgeIngest, _FakeTransport]:
    transport = _FakeTransport()
    return KnowledgeIngest(transport, loop=None), transport


@pytest.mark.asyncio
async def test_ingest_entities_writes_nodes_and_edges(ingest):
    service, transport = ingest
    res = await ingest_entities(
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
        ingest=service,
    )
    assert res == {"nodes": 2, "edges": 1}
    assert len(transport.requests) == 1
    request = transport.requests[0]
    record_ids = {record.record_id for record in request.records}
    assert record_ids == {"erpnext:customer:acme", "erpnext:salesorder:SO-1"}
    acme = next(r for r in request.records if r.record_id == "erpnext:customer:acme")
    assert acme.payload["name"] == "Acme"
    assert request.relationships[0].relation_reference.endswith(
        "resources/SalesOrder/relations/orderedBy"
    )


@pytest.mark.asyncio
async def test_ingest_sales_order_maps_customer_and_items(ingest):
    service, transport = ingest
    res = await ingest_doctype(
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
        ingest=service,
    )
    # SalesOrder + Customer + 2 Items = 4 nodes; orderedBy + 2 contains = 3 edges
    assert res == {"nodes": 4, "edges": 3}
    request = transport.requests[0]
    records = {record.record_id: record.payload for record in request.records}
    so = records["erpnext:salesorder:SO-2026-0001"]
    assert so["grandTotal"] == 1250.5
    assert so["docStatus"] == 1
    assert so["postingDate"] == "2026-07-04"
    assert "erpnext:customer:Acme_Corp" in records
    assert "erpnext:item:WIDGET-1" in records
    relation_pairs = {
        (rel.source.record_id, rel.target.record_id, rel.relation_reference.rsplit("/", 1)[-1])
        for rel in request.relationships
    }
    assert (
        "erpnext:salesorder:SO-2026-0001",
        "erpnext:customer:Acme_Corp",
        "orderedBy",
    ) in relation_pairs
    assert (
        "erpnext:salesorder:SO-2026-0001",
        "erpnext:item:WIDGET-1",
        "contains",
    ) in relation_pairs


@pytest.mark.asyncio
async def test_ingest_purchase_order_maps_supplier(ingest):
    service, transport = ingest
    res = await ingest_doctype(
        "Purchase Order",
        [{"name": "PO-1", "supplier": "Globex", "grand_total": 42.0, "docstatus": 0}],
        ingest=service,
    )
    assert res == {"nodes": 2, "edges": 1}
    request = transport.requests[0]
    records = {record.record_id: record.payload for record in request.records}
    assert "erpnext:purchaseorder:PO-1" in records
    assert "erpnext:supplier:Globex" in records
    relation_pairs = {
        (rel.source.record_id, rel.target.record_id, rel.relation_reference.rsplit("/", 1)[-1])
        for rel in request.relationships
    }
    assert (
        "erpnext:purchaseorder:PO-1",
        "erpnext:supplier:Globex",
        "suppliedBy",
    ) in relation_pairs


@pytest.mark.asyncio
async def test_ingest_employee_maps_department_link(ingest):
    service, transport = ingest
    res = await ingest_doctype(
        "Employee",
        [{"name": "HR-EMP-1", "employee_name": "Jane Doe", "department": "Sales"}],
        ingest=service,
    )
    assert res == {"nodes": 2, "edges": 1}
    request = transport.requests[0]
    records = {record.record_id: record.payload for record in request.records}
    assert records["erpnext:employee:HR-EMP-1"]["employeeName"] == "Jane Doe"
    assert "erpnext:orgunit:Sales" in records
    relation_pairs = {
        (rel.source.record_id, rel.target.record_id, rel.relation_reference.rsplit("/", 1)[-1])
        for rel in request.relationships
    }
    assert (
        "erpnext:employee:HR-EMP-1",
        "erpnext:orgunit:Sales",
        "memberOf",
    ) in relation_pairs


@pytest.mark.asyncio
async def test_ingest_item_catalog(ingest):
    service, transport = ingest
    res = await ingest_doctype(
        "Item",
        [
            {
                "name": "WIDGET-1",
                "item_code": "WIDGET-1",
                "item_name": "Widget",
                "item_group": "Products",
            }
        ],
        ingest=service,
    )
    assert res == {"nodes": 1, "edges": 0}
    request = transport.requests[0]
    records = {record.record_id: record.payload for record in request.records}
    assert records["erpnext:item:WIDGET-1"]["item_group"] == "Products"


@pytest.mark.asyncio
async def test_unsupported_doctype_is_rejected(ingest):
    service, _transport = ingest
    with pytest.raises(IngestError, match="unsupported ERPNext document type"):
        await ingest_doctype(
            "Journal Entry",
            [{"name": "JV-1"}],
            ingest=service,
        )


@pytest.mark.asyncio
async def test_missing_node_type_is_rejected(ingest):
    service, _transport = ingest
    with pytest.raises(IngestError):
        await ingest_entities(
            [{"id": "retired", "type": "RetiredAlias"}],
            ingest=service,
        )


@pytest.mark.asyncio
async def test_empty_ingest_is_rejected(ingest):
    service, _transport = ingest
    with pytest.raises(IngestError, match="at least one entity"):
        await ingest_entities([], ingest=service)
