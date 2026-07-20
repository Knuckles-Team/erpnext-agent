"""Native epistemic-graph ingestion for ERPNext / Frappe records.

CONCEPT:AU-KG.ingest.enterprise-source-extractor. Connector-specific mappers emit
canonical node_type nodes and relationship edges. The required agent-utilities
native-ingest primitive owns the transaction and raises NativeIngestError when the
authoritative engine cannot commit.
"""

from __future__ import annotations

from typing import Any

from agent_utilities.knowledge_graph.memory.native_ingest import (
    NativeIngestError,
)
from agent_utilities.knowledge_graph.memory.native_ingest import (
    ingest_documents as _native_ingest_documents,
)
from agent_utilities.knowledge_graph.memory.native_ingest import (
    ingest_entities as _native_ingest_entities,
)
from agent_utilities.knowledge_graph.memory.native_ingest import (
    media_store as _native_media_store,
)

_SOURCE = "erpnext-agent"
_DOMAIN = "erpnext"


def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Write canonical typed nodes and relationships through agent-utilities."""
    return _native_ingest_entities(
        entities,
        relationships,
        source=source,
        domain=domain,
        client=client,
        graph=graph,
    )


def ingest_documents(
    documents: list[dict[str, Any]],
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Write searchable documents through the authoritative native-ingest path."""
    return _native_ingest_documents(
        documents,
        source=source,
        domain=domain,
        client=client,
        graph=graph,
    )


def _slug(name: Any) -> str:
    """Normalise a Frappe primary key into an id-safe slug."""
    return str(name).strip().replace(" ", "_").replace("/", "-").replace(":", "-")


def media_store() -> Any:
    """Return the authoritative native media store."""
    return _native_media_store()


def ingest_attachment(
    name: Any,
    content: bytes,
    *,
    filename: str | None = None,
    content_type: str | None = None,
) -> str:
    """Store an ERPNext attachment, failing closed when content cannot be committed."""
    if not content:
        raise NativeIngestError("native ingest attachment requires content")
    stored = media_store().store_media(
        content,
        media_type="document",
        mime_type=content_type or "application/octet-stream",
        name=filename or f"erpnext-{_slug(name)}",
        source=_SOURCE,
        extra={"domain": _DOMAIN},
    )
    if stored is None:
        raise NativeIngestError("native attachment transaction failed")
    return stored.occurrence_id


# --- per-DocType mappers (records -> typed entity/relationship dicts) ---


def _party(record: dict[str, Any], cls: str, name_field: str, group_field: str) -> dict[str, Any]:
    name = record.get("name")
    return {
        "id": f"erpnext:{cls.lower()}:{_slug(name)}",
        "node_type": cls,
        "name": record.get(name_field) or name,
        "docName": name,
        "group": record.get(group_field),
        "territory": record.get("territory"),
        "disabled": record.get("disabled"),
        "externalToolId": str(name) if name is not None else None,
    }


def _line_items(
    parent_id: str, record: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Map a document's Frappe ``items`` child table -> :Item nodes + :contains edges."""
    items: list[dict[str, Any]] = []
    rels: list[dict[str, Any]] = []
    for row in record.get("items") or []:
        code = row.get("item_code") or row.get("item_name")
        if not code:
            continue
        iid = f"erpnext:item:{_slug(code)}"
        items.append(
            {
                "id": iid,
                "node_type": "Item",
                "name": row.get("item_name") or code,
                "item_code": code,
                "item_group": row.get("item_group"),
                "stock_uom": row.get("uom") or row.get("stock_uom"),
                "externalToolId": str(code),
            }
        )
        rels.append({"source": parent_id, "target": iid, "relationship": "contains"})
    return items, rels


def _order(
    record: dict[str, Any], cls: str, party_key: str, party_cls: str, party_rel: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    name = record.get("name")
    oid = f"erpnext:{cls.lower()}:{_slug(name)}"
    node = {
        "id": oid,
        "node_type": cls,
        "name": name,
        "grandTotal": record.get("grand_total") or record.get("rounded_total"),
        "docStatus": record.get("docstatus"),
        "postingDate": record.get("transaction_date") or record.get("posting_date"),
        "status": record.get("status"),
        "currency": record.get("currency"),
        "company": record.get("company"),
        "externalToolId": str(name) if name is not None else None,
    }
    entities = [node]
    rels: list[dict[str, Any]] = []
    party = record.get(party_key)
    if party:
        pid = f"erpnext:{party_cls.lower()}:{_slug(party)}"
        entities.append({"id": pid, "node_type": party_cls, "name": party, "externalToolId": str(party)})
        rels.append({"source": oid, "target": pid, "relationship": party_rel})
    line_items, line_rels = _line_items(oid, record)
    entities.extend(line_items)
    rels.extend(line_rels)
    return entities, rels


def _collect(
    records: list[dict[str, Any]],
    mapper,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    entities: list[dict[str, Any]] = []
    rels: list[dict[str, Any]] = []
    for rec in records or []:
        if not isinstance(rec, dict) or not rec.get("name"):
            continue
        out = mapper(rec)
        if isinstance(out, tuple):
            ents, rs = out
            entities.extend(ents)
            rels.extend(rs)
        else:
            entities.append(out)
    return entities, rels


# --- DocType -> (entities, relationships) dispatch ---

_DOCTYPE_MAPPERS = {
    "Customer": lambda recs: _collect(
        recs, lambda r: _party(r, "Customer", "customer_name", "customer_group")
    ),
    "Supplier": lambda recs: _collect(
        recs, lambda r: _party(r, "Supplier", "supplier_name", "supplier_group")
    ),
    "Item": lambda recs: _collect(
        recs,
        lambda r: {
            "id": f"erpnext:item:{_slug(r.get('item_code') or r.get('name'))}",
            "node_type": "Item",
            "name": r.get("item_name") or r.get("name"),
            "item_code": r.get("item_code") or r.get("name"),
            "item_group": r.get("item_group"),
            "stock_uom": r.get("stock_uom"),
            "externalToolId": str(r.get("item_code") or r.get("name")),
        },
    ),
    "Sales Order": lambda recs: _collect(
        recs, lambda r: _order(r, "SalesOrder", "customer", "Customer", "orderedBy")
    ),
    "Purchase Order": lambda recs: _collect(
        recs, lambda r: _order(r, "PurchaseOrder", "supplier", "Supplier", "suppliedBy")
    ),
    "Sales Invoice": lambda recs: _collect(
        recs, lambda r: _order(r, "Invoice", "customer", "Customer", "orderedBy")
    ),
    "Purchase Invoice": lambda recs: _collect(
        recs, lambda r: _order(r, "Invoice", "supplier", "Supplier", "suppliedBy")
    ),
    "Employee": lambda recs: _collect(
        recs,
        lambda r: (
            [
                {
                    "id": f"erpnext:employee:{_slug(r.get('name'))}",
                    "node_type": "Employee",
                    "name": r.get("employee_name") or r.get("name"),
                    "employeeName": r.get("employee_name"),
                    "designation": r.get("designation"),
                    "company": r.get("company"),
                    "status": r.get("status"),
                    "externalToolId": str(r.get("name")),
                }
            ]
            + (
                [
                    {
                        "id": f"erpnext:orgunit:{_slug(r.get('department'))}",
                        "node_type": "OrgUnit",
                        "name": r.get("department"),
                    }
                ]
                if r.get("department")
                else []
            ),
            (
                [
                    {
                        "source": f"erpnext:employee:{_slug(r.get('name'))}",
                        "target": f"erpnext:orgunit:{_slug(r.get('department'))}",
                        "relationship": "memberOf",
                    }
                ]
                if r.get("department")
                else []
            ),
        ),
    ),
}

# DocType -> id prefix, for callers / docs.
SUPPORTED_DOCTYPES = tuple(_DOCTYPE_MAPPERS)


def ingest_doctype(
    doctype: str,
    records: list[dict[str, Any]],
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Map a list of Frappe ``doctype`` records → typed nodes+links and ingest them.

    Supported doctypes: :data:`SUPPORTED_DOCTYPES`. Unsupported types fail closed.
    """
    mapper = _DOCTYPE_MAPPERS.get(doctype)
    if mapper is None:
        raise NativeIngestError("unsupported ERPNext document type")
    entities, relationships = mapper(records or [])
    return ingest_entities(entities, relationships, client=client, graph=graph)
