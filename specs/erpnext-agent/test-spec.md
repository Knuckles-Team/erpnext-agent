# CONN-ERPNEXT-AGENT — Test specification

| Case | Fixture/action | Expected result |
| --- | --- | --- |
| VER-T1 | Read `erpnext_agent.__version__` and the `pyproject.toml` project version | They are equal |
| OPS-T1 | Call each typed operation on `Api` with `request` patched | Each sends its one documented Frappe verb, path and parameters (`CONN-ERPNEXT-AGENT-R005`) |
| ERR-T1 | Build the error from a Frappe 417 body with `_server_messages` and `exc` | Message is `API error: 417 <exc_type>: <reason>`; no traceback text (`CONN-ERPNEXT-AGENT-R006`) |
| AC-T2 | Parse every access contract and list the served tools | Each contract's tool is served and its parameters are in the tool's input schema (`CONN-ERPNEXT-AGENT-R007`) |
| HR-T1 | Call each HR method on `Api` with `request` patched | Each sends its documented Frappe path, verb and body; submittable HR documents are submitted after insert; leave decisions set status then submit (`CONN-ERPNEXT-AGENT-R008`) |
| CRM-T1 | Call each CRM method on `Api` with `request` patched | Each sends its documented path and body; mapped drafts are completed and saved; communications are records only (`CONN-ERPNEXT-AGENT-R009`) |
| ONB-T1 | Plan, apply, apply again and verify a spec against an in-memory Frappe | The dry run writes nothing; apply creates each record once and verifies; the second apply writes nothing; the wizard runs only when planned and confirmed (`CONN-ERPNEXT-AGENT-R010`) |
| LIFE-T1 | Apply every state and event pair to `transition`; legal ids `draft-save`, `draft-submit`, `submitted-cancel`, `cancelled-amend` | Each legal pair returns its declared state; every other pair raises `IllegalTransition` with a reason code (`CONN-ERPNEXT-AGENT-R011.1`) |
| LIFE-T2 | Submit a Draft, a Submitted, a Cancelled and a non-submittable document with `request` patched | Only the Draft posts; the others raise before any POST (`CONN-ERPNEXT-AGENT-R011.2`) |
| LIFE-T3 | Cancel documents in each state, with submitted links, and with a stale `modified` | Only a linked-free, fresh Submitted document posts; each refusal names its reason (`CONN-ERPNEXT-AGENT-R011.3`) |
| LIFE-T4 | Amend a Draft, a Submitted and a Cancelled document | Only the Cancelled one yields a new Draft with `amended_from` (`CONN-ERPNEXT-AGENT-R011.4`) |
| LIFE-T5 | Ingest Sales Order records with docstatus 0, 1 and 2 | Nodes carry `documentState` Draft, Submitted, Cancelled and no raw integer (`CONN-ERPNEXT-AGENT-R011.5`) |
| LIFE-T6 | Call the served submit, cancel and amend tools in every state against the in-memory server | A refused call records zero write requests and the error carries the reason code (`CONN-ERPNEXT-AGENT-R011.6`) |
| LIFE-T7 | Build the descriptor and drive a governed proposal in every state | The descriptor equals the table; an illegal move or stale `modified` refuses with zero API calls (`CONN-ERPNEXT-AGENT-R011.7`) |

Proof: `tests/test_version.py::test_reported_version_matches_the_released_package` (`CONN-ERPNEXT-AGENT-R001`).
# Synthetic access contracts (CONN-ERPNEXT-AGENT-R002)

`tests/test_access_contracts.py::test_served_access_contracts_match_synthetic_provider`
compares the parsed contracts with the served synthetic supplier and purchase-order data.

## Rows awaiting bound tests
- `CONN-ERPNEXT-AGENT-R003`: planned proof `tests/test_access_contracts.py::test_supplier_rows_match_recorded_response`. Expected: rows read through the declared supplier contract equal the recorded response rows with key name and label supplier_name. Refusal: a row missing the key field name fails the comparison.
- `CONN-ERPNEXT-AGENT-R004`: planned proof `tests/test_access_contracts.py::test_supplier_and_purchase_order_fields_match_recorded_fixture`. Expected: the served tool returns exactly the contract fields for the recorded Supplier and Purchase Order rows. Refusal: a field outside the pinned contract set in the recorded row fails the exact-fields assertion.
