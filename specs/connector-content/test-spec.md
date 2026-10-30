# CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT — Test specification

Governing spec: [spec.md](spec.md).

| Test ID | Requirement | Proving test | Expected observation |
|---|---|---|---|
| T-001 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R001` | `tests/test_default_content_surfaces.py` | The listings include the packaged skills, ontology and prompts. |
| T-002 | `CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT-R002` | connector ontology certification | The connector manifest gate passes; none of the four is `UNRESOLVED`. |
