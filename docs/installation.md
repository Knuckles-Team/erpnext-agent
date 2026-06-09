# Installation

`erpnext-agent` is a standard Python package and a prebuilt container image. Pick the
path that matches how you want to run it.

## Requirements

- **Python 3.11 – 3.14**.
- A reachable **ERPNext / Frappe site** — see [Backing Platform](platform.md) to
  deploy one locally.

## From PyPI (recommended)

```bash
pip install erpnext-agent
```

### Optional extras

The base install is intentionally minimal. Install the extra for what you need:

| Extra | Install | Pulls in |
|---|---|---|
| `mcp` | `pip install "erpnext-agent[mcp]"` | FastMCP MCP-server runtime (`agent-utilities[mcp]`) |
| `agent` | `pip install "erpnext-agent[agent]"` | Pydantic-AI agent server + Logfire tracing |
| `all` | `pip install "erpnext-agent[all]"` | Everything above |
| `test` | `pip install "erpnext-agent[test]"` | `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-xdist` |

```bash
# Typical: run the MCP server and the agent server
pip install "erpnext-agent[all]"
```

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

A multi-stage, slim image is published on every release (installs
`erpnext-agent[all]`, entrypoint `erpnext-mcp`):

```bash
docker pull knucklessg1/erpnext-agent:latest

docker run --rm -i \
  -e ERPNEXT_URL=https://your-erpnext:8000 \
  -e ERPNEXT_TOKEN=your_api_key:your_api_secret \
  knucklessg1/erpnext-agent:latest        # stdio transport (default)
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
