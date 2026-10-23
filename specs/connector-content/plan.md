# CONN-ERPNEXT-AGENT-CONNECTOR-CONTENT — Design and implementation plan

Governing spec: [spec.md](spec.md).

## Architecture

`pyproject.toml` declares `erpnext-mcp` as the connector identity. `create_mcp_server` resolves the packaged content of `erpnext_agent` from it.
