"""MCP tool for native epistemic-graph ingestion of ERPNext DocType records.

CONCEPT:AU-KG.ingest.enterprise-source-extractor. Wire-First: lists a Frappe DocType
via the existing client and natively pushes the records into the knowledge graph as
typed OWL nodes (:Customer/:Supplier/:Item/:SalesOrder/:PurchaseOrder/:Invoice/:Employee).
Best-effort — returns ``{"ingested": None}`` when no engine is reachable.
"""

from fastmcp import Context, FastMCP
from fastmcp.dependencies import Depends
from pydantic import Field

from erpnext_agent.auth import get_client


def register_ingest_tools(mcp: FastMCP):
    """Register the ERPNext KG-ingestion tool."""

    @mcp.tool(tags={"ingest", "kg"})
    async def erpnext_ingest(
        doctype: str = Field(
            default="Sales Order",
            description=(
                "Frappe DocType to list and ingest. One of: Customer, Supplier, Item, "
                "Sales Order, Purchase Order, Sales Invoice, Purchase Invoice, Employee."
            ),
        ),
        params_json: str = Field(
            default="{}",
            description=(
                "JSON string of list_documents kwargs (filters, fields, limit, "
                "limit_page_length, limit_start)."
            ),
        ),
        client=Depends(get_client),
        ctx: Context | None = Field(default=None, description="MCP context"),
    ) -> dict:
        """Natively ingest an ERPNext DocType into epistemic-graph as typed nodes.

        Lists records via the Frappe REST client and pushes them (with their party /
        line-item / department links) into the knowledge graph via the fast engine
        client. CONCEPT:AU-KG.ingest.enterprise-source-extractor.
        """
        import json as _json

        from erpnext_agent.kg_ingest import ingest_doctype

        if ctx:
            await ctx.info(f"Ingesting ERPNext {doctype} into the knowledge graph...")
        try:
            kwargs = _json.loads(params_json) if params_json else {}
        except Exception as e:  # noqa: BLE001
            return {"error": f"Invalid params_json: {e}"}
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

        try:
            resp = client.list_documents(doctype, **kwargs)
        except Exception as e:  # noqa: BLE001
            return {"error": f"Failed to list {doctype}: {e}"}

        if isinstance(resp, dict):
            records = resp.get("data", resp.get("result", []))
        else:
            records = resp
        if not isinstance(records, list):
            records = [records] if records else []

        result = ingest_doctype(doctype, records)
        return {"doctype": doctype, "listed": len(records), "ingested": result}

    return None
