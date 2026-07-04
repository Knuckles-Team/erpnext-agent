"""Native epistemic-graph ingestion for ERPNext / Frappe records (typed graph nodes).

CONCEPT:AU-KG.ingest.enterprise-source-extractor. The record-source twin of
media-downloader's blob ingestion: erpnext-agent natively pushes its Frappe DocType
data into the ONE epistemic-graph knowledge graph as **typed OWL nodes**
(``:Customer``, ``:Supplier``, ``:Item``, ``:SalesOrder``, ``:PurchaseOrder``,
``:Invoice``, ``:Employee``) + links, plus text-y notes as ``:Document`` nodes and
attachments/print PDFs as raw ``:Blob``/``:MediaAsset`` via :func:`media_store`.

It prefers the shared fleet primitive
``agent_utilities.knowledge_graph.memory.native_ingest`` (the ONE txn write path);
that import is GUARDED so with no KG stack / no reachable engine every entry point
**no-ops** (returns ``None``) and the connector keeps working with zero KG
infrastructure. Node ids follow ``erpnext:<class>:<name>`` and every ``type`` matches
a class the package's :mod:`erpnext_agent.ontology` ``.ttl`` federates.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("erpnext_agent.kg")

_SOURCE = "erpnext-agent"
_DOMAIN = "erpnext"


def _shared():
    """Return the shared native-ingest module, or ``None`` when it isn't installed.

    Prefer the ONE fleet primitive
    ``agent_utilities.knowledge_graph.memory.native_ingest``; when the hub predates it
    we fall back to the identical local txn-writer below so ingestion still works.
    """
    try:
        from agent_utilities.knowledge_graph.memory import native_ingest
    except Exception as e:  # noqa: BLE001 — hub predates the shared primitive
        logger.debug("erpnext KG ingest: shared primitive absent (%s); using local writer", e)
        return None
    return native_ingest


def _local_client() -> tuple[Any | None, str]:
    """Local fallback: resolve the fast engine client, or ``(None, "")`` if unavailable."""
    try:
        from agent_utilities.knowledge_graph.core.graph_compute import (
            GraphComputeEngine,
        )
    except Exception as e:  # noqa: BLE001 — KG stack absent
        logger.debug("erpnext KG ingest unavailable (import): %s", e)
        return None, ""
    try:
        engine = GraphComputeEngine()
        client = getattr(engine, "_client", None)
        if client is None:
            return None, ""
        return client, (getattr(engine, "graph_name", None) or "__commons__")
    except Exception as e:  # noqa: BLE001 — engine unreachable
        logger.debug("erpnext KG ingest: engine unreachable: %s", e)
        return None, ""


def _local_write(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None,
    *,
    client: Any | None,
    graph: str | None,
) -> dict[str, int] | None:
    """Local mirror of the shared txn dance (used only when the primitive is absent)."""
    if client is None:
        client, graph = _local_client()
    if client is None:
        return None
    graph = graph or "__commons__"
    try:
        txn = client.txn.begin(graph=graph)
        for ent in entities:
            props = {k: v for k, v in ent.items() if k != "id" and v is not None}
            props.setdefault("source", _SOURCE)
            props.setdefault("domain", _DOMAIN)
            client.txn.add_node(txn, ent["id"], props)
        committed = client.txn.commit(txn)
    except Exception as e:  # noqa: BLE001 — engine/txn failure is non-fatal
        logger.warning("erpnext KG ingest: txn failed: %s", e)
        return None
    if not committed:
        logger.warning("erpnext KG ingest: txn not committed (conflict)")
        return None
    edges = 0
    for rel in relationships or []:
        try:
            client.edges.add(
                rel["source"], rel["target"], {"type": rel.get("type", "RELATED")}
            )
            edges += 1
        except Exception as e:  # noqa: BLE001 — pure edge link, best-effort
            logger.debug("erpnext KG ingest: edge skipped: %s", e)
    logger.info("erpnext KG ingest: wrote %d nodes, %d edges", len(entities), edges)
    return {"nodes": len(entities), "edges": edges}


def _slug(name: Any) -> str:
    """Normalise a Frappe ``name`` (primary key) into an id-safe slug."""
    return str(name).strip().replace(" ", "_").replace("/", "-").replace(":", "-")


def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Write typed ERPNext nodes (+ edges) into epistemic-graph. Best-effort no-op."""
    entities = [e for e in (entities or []) if e.get("id")]
    if not entities:
        return None
    shared = _shared()
    if shared is not None:
        return shared.ingest_entities(
            entities,
            relationships or [],
            source=_SOURCE,
            domain=_DOMAIN,
            client=client,
            graph=graph,
        )
    return _local_write(entities, relationships, client=client, graph=graph)


def ingest_documents(
    documents: list[dict[str, Any]],
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Write text-y ERPNext notes/descriptions as ``:Document`` nodes. Best-effort no-op."""
    import time

    documents = [d for d in (documents or []) if d.get("id") and (d.get("text") or d.get("content"))]
    if not documents:
        return None
    shared = _shared()
    if shared is not None:
        return shared.ingest_documents(
            documents, source=_SOURCE, domain=_DOMAIN, client=client, graph=graph
        )
    # Local fallback: shape docs as :Document nodes then reuse the local writer.
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    nodes: list[dict[str, Any]] = []
    for doc in documents:
        node = {k: v for k, v in doc.items() if k != "content" and v is not None}
        node["type"] = "Document"
        node["text"] = doc.get("text") or doc.get("content")
        node.setdefault("created_at", now)
        nodes.append(node)
    return _local_write(nodes, None, client=client, graph=graph)


def media_store() -> Any | None:
    """Return a live blob store for ERPNext attachments / print-format PDFs, or ``None``."""
    shared = _shared()
    if shared is not None:
        return shared.media_store()
    client, _ = _local_client()
    if client is None:
        return None
    try:
        from agent_utilities.knowledge_graph.core.graph_compute import (
            GraphComputeEngine,
        )
        from agent_utilities.knowledge_graph.memory.media_store import MediaStore

        return MediaStore(GraphComputeEngine())
    except Exception as e:  # noqa: BLE001 — blob store optional
        logger.debug("erpnext KG ingest: media_store unavailable: %s", e)
        return None


def ingest_attachment(
    name: Any,
    content: bytes,
    *,
    filename: str | None = None,
    content_type: str | None = None,
) -> str | None:
    """Push a raw ERPNext attachment / print-format PDF into the KG as a blob.

    Returns the stored blob id/hash, or ``None`` when no engine is reachable. Never raises.
    """
    if not content:
        return None
    store = media_store()
    if store is None:
        return None
    try:
        return store.put(  # type: ignore[no-any-return]
            content,
            filename=filename or f"erpnext-{_slug(name)}",
            content_type=content_type or "application/octet-stream",
            source=_SOURCE,
            domain=_DOMAIN,
        )
    except Exception as e:  # noqa: BLE001 — blob store best-effort
        logger.debug("erpnext KG ingest: attachment skipped: %s", e)
        return None


# --- per-DocType mappers (records -> typed entity/relationship dicts) ---


def _party(record: dict[str, Any], cls: str, name_field: str, group_field: str) -> dict[str, Any]:
    name = record.get("name")
    return {
        "id": f"erpnext:{cls.lower()}:{_slug(name)}",
        "type": cls,
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
                "type": "Item",
                "name": row.get("item_name") or code,
                "item_code": code,
                "item_group": row.get("item_group"),
                "stock_uom": row.get("uom") or row.get("stock_uom"),
                "externalToolId": str(code),
            }
        )
        rels.append({"source": parent_id, "target": iid, "type": "contains"})
    return items, rels


def _order(
    record: dict[str, Any], cls: str, party_key: str, party_cls: str, party_rel: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    name = record.get("name")
    oid = f"erpnext:{cls.lower()}:{_slug(name)}"
    node = {
        "id": oid,
        "type": cls,
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
        entities.append({"id": pid, "type": party_cls, "name": party, "externalToolId": str(party)})
        rels.append({"source": oid, "target": pid, "type": party_rel})
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
            "type": "Item",
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
                    "type": "Employee",
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
                        "type": "OrgUnit",
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
                        "type": "memberOf",
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
) -> dict[str, int] | None:
    """Map a list of Frappe ``doctype`` records → typed nodes+links and ingest them.

    Supported doctypes: :data:`SUPPORTED_DOCTYPES`. Returns ``{"nodes":n,"edges":m}``
    or ``None`` (unsupported doctype / no engine / empty). Never raises.
    """
    mapper = _DOCTYPE_MAPPERS.get(doctype)
    if mapper is None:
        logger.debug("erpnext KG ingest: unsupported doctype %r", doctype)
        return None
    entities, relationships = mapper(records or [])
    return ingest_entities(entities, relationships, client=client, graph=graph)
