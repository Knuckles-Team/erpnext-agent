"""The access contracts describe fields served by the typed list tool."""

import asyncio
import json
from pathlib import Path

import pytest
from fastmcp import Client
from scion_sdk.access_contract import parse_access_contracts

from erpnext_agent.api_client import Api

ROOT = Path(__file__).resolve().parents[1]


def _served_server(monkeypatch):
    from scion_sdk._connector_serve import build_server

    monkeypatch.setenv("ERPNEXT_URL", "https://service.invalid")
    monkeypatch.setenv("AUTH_TYPE", "none")
    _, mcp = build_server("erpnext_agent", command_args=["--transport", "stdio"])
    return mcp


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
    monkeypatch.setattr(
        Api, "list_documents", lambda self, doctype, **_: {"data": [samples[doctype]]}
    )
    mcp = _served_server(monkeypatch)

    async def run():
        async with Client(mcp) as client:
            served = {tool.name for tool in await client.list_tools()}
            for contract in selected:
                assert contract.operation == "erpnext_list_documents"
                assert contract.operation in served
                result = await client.call_tool(
                    contract.operation, {"doctype": contract.entity}
                )
                assert not result.is_error
                record = json.loads(result.content[0].text)["data"][0]
                assert record == samples[contract.entity]
                assert {field for _, field in contract.predicates} == expected[
                    contract.entity
                ]
                assert contract.key_field in record
                assert all(field in record for _, field in contract.predicates)

    asyncio.run(run())


@pytest.mark.spec("CONN-ERPNEXT-AGENT-R007")
def test_every_access_contract_names_a_served_tool_and_its_parameters(monkeypatch):
    contracts = parse_access_contracts(
        (ROOT / "erpnext_agent/ontology/access_contracts.ttl").read_text()
    )
    mcp = _served_server(monkeypatch)

    async def run():
        async with Client(mcp) as client:
            tools = {tool.name: tool for tool in await client.list_tools()}
            for contract in contracts:
                tool = tools[contract.operation]
                params = set(tool.input_schema["properties"])
                assert set(contract.parameters) <= params, contract.entity

    asyncio.run(run())
