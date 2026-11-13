import pytest

from erpnext_agent.connector_sources import SCHEMA_MAPPINGS


@pytest.mark.spec("CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R002")
def test_four_doctypes_map_to_core_classes():
    assert {
        k: SCHEMA_MAPPINGS[k]["ontology_class"]
        for k in ("Supplier", "Item", "PurchaseOrder", "Customer")
    } == {
        "Supplier": "Supplier",
        "Item": "SupplyChainItem",
        "PurchaseOrder": "PurchaseOrder",
        "Customer": "Customer",
    }
