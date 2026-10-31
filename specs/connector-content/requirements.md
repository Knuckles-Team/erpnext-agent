# CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT — Requirements

Governing spec: [spec.md](spec.md).

Each row is one requirement. A row names the file it touches and the test that proves it. The generator sets each row's state in `status.json`.

| ID | Requirement | Acceptance |
|---|---|---|
| `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R001` | **Default content.** `pyproject.toml` declares `erpnext-mcp` as the single `scion_sdk.connector` entry point. The server lists the packaged `skill://` and `ontology://` resources and the packaged prompts with no `content=` argument. Proving test: `tests/test_default_content_surfaces.py`. | `resources/list` includes `skill://` and `ontology://`; `prompts/list` includes each packaged prompt. |
| `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R002` | **Resolve the manifest ontology classes for supplier, item, purchase order and customer.** Subsystem: connector `erpnext-agent`. In `erpnext-agent/connector_manifest.yml` set `ontology_class` of `Supplier`, `Item`, `PurchaseOrder` and `Customer` to the medulla core classes. Regenerate the manifest with the connector manifest generator; never edit it by hand. The consumer is the medulla supply-chain fixture EG-SUPPLY-VOCAB-R005.6. | Test: the connector manifest gate passes and `tests/test_manifest_classes.py::test_no_unresolved_for_the_four` (L2) finds no `UNRESOLVED` value for the four classes. |
