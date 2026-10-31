"""The access contracts describe fields served by the resource tool."""

import asyncio
import json
from pathlib import Path

import pytest
from fastmcp import Client, FastMCP
from scion_sdk.access_contract import parse_access_contracts

from erpnext_agent.api_client import Api
from erpnext_agent.mcp.mcp_resource import register_resource_tools

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R002")
def test_served_access_contracts_match_synthetic_provider(monkeypatch):
    """These fixtures are synthetic; they are not production recordings."""
    samples = {
        "Supplier": {"name": "SUP-001", "supplier_name": "Example Supplier"},
        "Purchase Order": {"name": "PO-001", "grand_total": 42.5, "docstatus": 1},
    }
    contracts = parse_access_contracts(
        (ROOT / "erpnext_agent/ontology/access_contracts.ttl").read_text()
    )
    selected = [contract for contract in contracts if contract.entity in samples]
    assert {contract.entity for contract in selected} == set(samples)
    expected = {
        "Supplier": {"supplier_name"},
        "Purchase Order": {"grand_total", "docstatus"},
    }
    monkeypatch.setenv("ERPNEXT_URL", "https://service.invalid")
    monkeypatch.setattr(Api, "list_documents", lambda self, doctype: [samples[doctype]])

    async def run():
        server = FastMCP("erpnext-fixture")
        register_resource_tools(server)
        async with Client(server) as client:
            for contract in selected:
                assert contract.operation == "erpnext_agent_resource"
                result = await client.call_tool(
                    contract.operation,
                    {
                        "action": "list_documents",
                        "params_json": json.dumps({"doctype": contract.entity}),
                    },
                )
                assert not result.is_error
                record = json.loads(result.content[0].text)["result"][0]
                assert record == samples[contract.entity]
                assert {field for _, field in contract.predicates} == expected[
                    contract.entity
                ]
                assert contract.key_field in record
                assert all(field in record for _, field in contract.predicates)

    asyncio.run(run())
