# Installation

`erpnext-agent` is a standard Python package and a prebuilt container image. Pick the
path that matches how the operator want to run it.

## Requirements

- **Python 3.11 – 3.14**.
- A reachable **ERPNext / Frappe site** — see [Backing Platform](platform.md) to
  deploy one locally.

## From PyPI (recommended)

```bash
pip install erpnext-agent
```

### Optional extras

The base install is intentionally minimal. Install the extra for what the operator need:

| Extra | Install | Pulls in |
|---|---|---|
| `mcp` | `pip install "erpnext-agent[mcp]"` | FastMCP MCP-server runtime (`agent-connector-sdk`) |
| `all` | `pip install "erpnext-agent[all]"` | Everything above |
| `test` | `pip install "erpnext-agent[test]"` | `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-xdist` |

## From source

```bash
git clone https://github.com/Knuckles-Team/erpnext-agent.git
cd erpnext-agent
pip install -e ".[all]"          # editable install with every extra
```

With [`uv`](https://docs.astral.sh/uv/):

```bash
uv pip install -e ".[all]"
uv run erpnext-mcp
```

## Prebuilt Docker image

A multi-stage runtime image is published on every release (installs
`erpnext-agent[all]`, entrypoint `erpnext-mcp`):

```bash
docker pull example/erpnext-agent@sha256:<digest>

docker run --rm -i \
  -e ERPNEXT_URL=<configured-endpoint> \
  -e ERPNEXT_TOKEN=<runtime-secret> \
  example/erpnext-agent@sha256:<digest>        # stdio transport (default)
```

For an HTTP server with a published port, see [Deployment](deployment.md).

## Verify the install

```bash
erpnext-mcp --help
python -c "import erpnext_agent; print(erpnext_agent.__version__)"
```

## Next steps

- **[Deployment](deployment.md)** — run it as a long-lived MCP server behind Caddy + DNS.
- **[Usage](usage.md)** — call the tools, the API, and example prompts.
- **[Configuration](deployment.md#configuration-environment)** — every environment variable.

### Optional transactional invoice app

Invoice creation through the enterprise interchange requires the optional
`scion_erp_guard` app installed on the Frappe site. Installing the MCP package
alone does not install a Frappe app. The site operator installs the standalone `frappe_app` package in
the site's Frappe environment, adds `scion_erp_guard` to the bench app list,
and runs `bench --site <site> install-app scion_erp_guard`. The operator must
also configure the site setting `scion_invoice_tenant_bindings`: a mapping from
each authorized Frappe API user to exactly one tenant identifier. Missing or
mismatched bindings refuse the call. The user still needs ERPNext permissions
to create and read the invoice.

The POST-only RPC endpoints are `scion_erp_guard.api.reserve_invoice`,
`scion_erp_guard.api.create_invoice_once` and
`scion_erp_guard.api.reconcile_invoice`. The site must preserve
Frappe's request transaction and the unique claim table. Custom hooks that commit independently or trigger external effects invalidate
the atomicity assumption. A missing claim
returns `unknown`; it never authorizes an automatic retry. Installing this app
is an operator action and does not itself authorize a connector or an invoice.

The connector transport requires an SDK version that verifies durable approval
before any source access. The current published SDK version does not establish
that ordering for every writer, so do not activate this transport until that
SDK prerequisite is released and the source app is qualified on the site.
A committed reservation is no-effect evidence only after reconciliation locks
the same source row that the create operation locks.
