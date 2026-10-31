# CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT — Requirements

Governing spec: [spec.md](spec.md).

Each row is one requirement. A row names the file it touches and the test that proves it. The generator sets each row's state in `status.json`.

| ID | Requirement | Acceptance |
|---|---|---|
| `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R001` | **Default content.** `pyproject.toml` declares `erpnext-mcp` as the single `agent_connector_sdk.connector` entry point. The server lists the packaged `skill://` and `ontology://` resources and the packaged prompts with no `content=` argument. Proving test: `tests/test_default_content_surfaces.py`. | `resources/list` includes `skill://` and `ontology://`; `prompts/list` includes each packaged prompt. |
| `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R002` | **Resolve manifest classes.** In `connector_manifest.yml` set `Supplier`, `Item`, `PurchaseOrder` and `Customer` `ontology_class` to the medulla core classes through the manifest generator, never by hand. Cites the medulla mapping rows `MEDULLA-SUPPLY-VOCAB-R005.1` and `MEDULLA-SUPPLY-VOCAB-R005.2`. | The connector manifest gate passes; none of the four is `UNRESOLVED`. |
