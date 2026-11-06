# CONN-ERPNEXT-AGENT — Test specification

| Case | Fixture/action | Expected result |
| --- | --- | --- |
| VER-T1 | Read `erpnext_agent.__version__` and the `pyproject.toml` project version | They are equal |
| OPS-T1 | Call each typed operation on `Api` with `request` patched | Each sends its one documented Frappe verb, path and parameters (`CONN-ERPNEXT-AGENT-R005`) |
| ERR-T1 | Build the error from a Frappe 417 body with `_server_messages` and `exc` | Message is `API error: 417 <exc_type>: <reason>`; no traceback text (`CONN-ERPNEXT-AGENT-R006`) |
| AC-T2 | Parse every access contract and list the served tools | Each contract's tool is served and its parameters are in the tool's input schema (`CONN-ERPNEXT-AGENT-R007`) |

Proof: `tests/test_version.py::test_reported_version_matches_the_released_package` (`CONN-ERPNEXT-AGENT-R001`).
# Synthetic access contracts (CONN-ERPNEXT-AGENT-R002)

`tests/test_access_contracts.py::test_served_access_contracts_match_synthetic_provider`
compares the parsed contracts with the served synthetic supplier and purchase-order data.

## Rows awaiting bound tests
- `CONN-ERPNEXT-AGENT-R003`: planned proof `tests/test_access_contracts.py::test_supplier_rows_match_recorded_response`. Expected: rows read through the declared supplier contract equal the recorded response rows with key name and label supplier_name. Refusal: a row missing the key field name fails the comparison.
- `CONN-ERPNEXT-AGENT-R004`: planned proof `tests/test_access_contracts.py::test_supplier_and_purchase_order_fields_match_recorded_fixture`. Expected: the served tool returns exactly the contract fields for the recorded Supplier and Purchase Order rows. Refusal: a field outside the pinned contract set in the recorded row fails the exact-fields assertion.
