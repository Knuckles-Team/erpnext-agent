---
name: erpnext-agent-development
domain: development
skill_type: skill
description: >-
  Develop, test, gate, and release the erpnext-agent connector. Use this skill
  when changing ERPNext/Frappe resource mappings, governed MCP tools,
  knowledge-graph ingestion, packaged connector content, documentation, or
  repository gates.
license: MIT
tags: [erpnext, frappe, development, connector, mcp, test, gates]
tier: repository
metadata:
  author: ERPNext contributors
  version: '0.1.0'
---

# erpnext-agent development

This repository owns the ERPNext/Frappe REST client, document resource mappings,
action-routed MCP tools, source declarations and knowledge-graph ingestion, and
packaged connector content. Shared connector contracts, transports, TLS profiles,
and credential helpers belong to `scion-sdk`; admission, serving, and
durable graph state belong to their owning repositories. Read `AGENTS.md` before
changing code and keep credentials, private endpoints, tenant data, and customer
records out of source, logs, fixtures, and skill content.

## Rapid delivery: the 5-minute contract

Specs are already designed. Deliver small, reviewable slices and cite the
owning spec row in the commit trailer.

- Find the owning row first with `git grep -n "<term>" -- specs` and extend the
  existing spec before adding requirement text. `PIPE-CONNSPEC-R119.4` is a
  central pipelines criterion; do not invent a local status row for it.
- Reuse the one `Connector` in `erpnext_agent/__init__.py`, the `Api` facade in
  `erpnext_agent/api_client.py`, and the resource client in
  `erpnext_agent/api/api_client_resource.py` over the shared
  `erpnext_agent/api/api_client_base.py` boundary. Do not create a second API,
  MCP, authentication, or transport plane.
- Preserve `ERPNEXT_URL`, `ERPNEXT_TOKEN`,
  `ERPNEXT_AGENT_USERNAME`, and `ERPNEXT_AGENT_PASSWORD` handling in
  `erpnext_agent/auth.py`, together with the SDK TLS resolver for
  `erpnext_agent`. Never hardcode a secret, endpoint, tenant, or TLS-verification
  bypass.
- Keep the action-routed registrations in
  `erpnext_agent/mcp/mcp_authentication.py`, `erpnext_agent/mcp/mcp_resource.py`,
  and `erpnext_agent/mcp/mcp_ingest.py` aligned with the registry in
  `erpnext_agent/mcp_server.py`. Preserve source declarations in
  `erpnext_agent/connector_sources.py` and typed mappings in
  `erpnext_agent/kg_ingest.py`; keep tenant and installation data neutral.
- Every delivered requirement needs a bound focused test. Generated
  `specs/*/status.json` files come from the shared hooks; never hand-edit them.
- Keep `erpnext_agent/skills/`, `erpnext_agent/ontology/`, prompts,
  `mcp_config.json`, and source declarations coherent with the existing
  package-data and `erpnext-mcp` entry point. One logical change per commit, with
  the central criterion recorded using the repository's documented
  `Spec: none (<reason>)` form when no local requirements row exists, plus the
  assisting-agent trailer.

## Setup and gates

Use the pinned environment from `uv sync --locked`, then run the shared gates:

```bash
uv sync --locked
uvx pre-commit run --all-files
uvx pre-commit run --all-files --hook-stage pre-push
```

For focused feedback, run the smallest affected test with the locked
environment:

```bash
uv run --locked --extra test pytest -q tests/test_erpnext_development_skill.py
```

The canonical `.pre-commit-config.yaml` delegates connector-standard, secrets,
spec, tests-fast, and dependency-readiness checks to
`Knuckles-Team/pipelines` at `rev: main`. Do not copy those hooks locally or
bypass a failing check.

## Connector-specific checks

- Keep ERPNext document CRUD, authentication, and pagination behind the one
  `Api` facade. Validate Frappe responses at the existing client boundary and
  preserve the established error behavior.
- Preserve SDK TLS resolution and token/basic-auth handling. Mock ERPNext HTTP
  responses in local tests; never call a live site or use live credentials in a
  gate.
- Keep `erpnext_agent/skills/`, `erpnext_agent/ontology/`,
  `erpnext_agent/connectors/` (when present), prompts, and `mcp_config.json` in
  package data. Keep source declarations and ontology mappings explicit and
  installation-neutral.
- Documentation is published by `.github/workflows/pages.yml`, which calls
  `pages_pipeline.yml@main` with the canonical spec dashboard config. The Python release and rendered connector
  image are called by `.github/workflows/pipeline.yml`; do not add a second
  publisher or commit generated Docker artifacts.

## Packaging and publication

`pyproject.toml` declares
`erpnext-mcp = "erpnext_agent:connector"` and packages `skills/**`, prompts,
ontology, connector content, `agent_data/**`, and `mcp_config.json`. For a
genuine packaged-content release, keep the project version, `CHANGELOG.md`, and
the editable `erpnext-agent` entry in `uv.lock` coherent, then inspect `uv build`
output for
`erpnext_agent/skills/erpnext-agent-development/SKILL.md`.

The canonical release caller is `.github/workflows/pipeline.yml`: it publishes
the Python connector with `python_pipeline.yml@main`, then builds the rendered
connector container with `container_pipeline.yml@main` and
`render_connector: true`. Do not claim package, container, or Pages publication
from a local build; require exact-source hosted evidence and the public artifact.

## Delivery discipline

Work in a real Git worktree based on `origin/main`. Inspect the complete diff,
stage only reviewed paths, and verify `git status --short` after every gate.
Do not use `git stash`, `git add -A`, or `git add .`; preserve unrelated working
tree changes. Keep runtime, ontology, source status, and generated artifacts
outside a bounded skill slice unless the owning requirement explicitly requires
them.
