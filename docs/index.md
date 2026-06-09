# erpnext-agent

ERPNext and Frappe **REST/RPC API + MCP Server** for the agent-utilities ecosystem
— a typed, deterministic tool surface over the ERPNext / Frappe business platform.

!!! info "Official documentation"
    This site is the canonical reference for `erpnext-agent`, maintained alongside
    every release.

[![PyPI](https://img.shields.io/pypi/v/erpnext-agent)](https://pypi.org/project/erpnext-agent/)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
[![License](https://img.shields.io/pypi/l/erpnext-agent)](https://github.com/Knuckles-Team/erpnext-agent/blob/main/LICENSE)
[![GitHub](https://img.shields.io/badge/source-GitHub-181717?logo=github)](https://github.com/Knuckles-Team/erpnext-agent)

## Overview

`erpnext-agent` wraps the ERPNext / Frappe Framework REST and whitelisted-RPC
surface with typed, deterministic MCP tools, and ships an optional Pydantic-AI
agent server for conversational workflows. It provides:

- **`Api`** — a tolerant `requests`-based REST/RPC facade over the Frappe site
  (token or username/password authentication, configurable TLS verification).
- **Document and method tools** — read, create, update, delete, and list any
  ERPNext DocType, plus `call_method` to invoke any whitelisted RPC endpoint
  (covering custom server functions).
- **An MCP server** (`erpnext-mcp`) and a companion **agent server**
  (`erpnext-agent`) that calls those tools through a policy router.

The connector remains inactive when credentials are absent, so it is safe to load
in any environment.

## Explore the documentation

<div class="grid cards" markdown>

- :material-rocket-launch: **[Installation](installation.md)** — pip, source, extras, and the prebuilt Docker image.
- :material-server-network: **[Deployment](deployment.md)** — run the MCP and agent servers, Docker Compose, Caddy + Technitium.
- :material-console: **[Usage](usage.md)** — the MCP tools, the `Api` client, and example prompts.
- :material-database-cog: **[Backing Platform](platform.md)** — deploy ERPNext / Frappe with Docker.
- :material-sitemap: **[Overview](overview.md)** — the dynamic facade and FastMCP tool layer.
- :material-tag-multiple: **[Concepts](concepts.md)** — the `CONCEPT:ERPN-*` registry.

</div>

## Quick start

```bash
pip install "erpnext-agent[mcp]"
erpnext-mcp                       # stdio MCP server (default transport)
```

Connect it to an ERPNext / Frappe site:

```bash
export ERPNEXT_URL=https://your-erpnext:8000
export ERPNEXT_TOKEN=your_api_key:your_api_secret
erpnext-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

See **[Installation](installation.md)** and **[Deployment](deployment.md)** for the
full matrix (PyPI extras, Docker image, all transports, reverse proxy, DNS).
