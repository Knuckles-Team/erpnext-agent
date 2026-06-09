# Deployment

This page covers running `erpnext-agent` as a long-lived server: the transports, a
Docker Compose stack, putting it behind a Caddy reverse proxy, and giving it a DNS
name with Technitium. To provision the **ERPNext / Frappe site** it connects to, see
[Backing Platform](platform.md).

> `erpnext-agent` ships **two** console scripts: an **MCP server** (`erpnext-mcp`)
> that exposes a typed, deterministic tool surface a policy router / agent calls, and
> an optional **A2A agent server** (`erpnext-agent`) that wraps those tools in a
> Pydantic-AI agent. Most deployments run the MCP server; the agent server is
> documented in [Agent server](#agent-server) below.

## Run the MCP server

The transport is selected with `--transport` (or the `TRANSPORT` env var):

=== "stdio (default)"

    ```bash
    erpnext-mcp
    ```
    For IDE / desktop MCP clients that launch the server as a subprocess.

=== "streamable-http"

    ```bash
    erpnext-mcp --transport streamable-http --host 0.0.0.0 --port 8000
    ```
    A network server with a `/health` endpoint and `/mcp` route.

=== "sse"

    ```bash
    erpnext-mcp --transport sse --host 0.0.0.0 --port 8000
    ```

Health check (HTTP transports):

```bash
curl -s http://localhost:8000/health        # {"status":"OK"}
```

## Configuration (environment)

`erpnext-agent` is configured entirely from the environment. The **required** set:

| Var | Default | Meaning |
|---|---|---|
| `ERPNEXT_URL` | `http://localhost:8000` | ERPNext / Frappe site base URL |
| `ERPNEXT_TOKEN` | _(empty)_ | API token in `api_key:api_secret` form |

Optional connection and runtime settings:

| Var | Default | Meaning |
|---|---|---|
| `ERPNEXT_AGENT_USERNAME` | _(empty)_ | Username for session login (alternative to a token) |
| `ERPNEXT_AGENT_PASSWORD` | _(empty)_ | Password for session login |
| `ERPNEXT_AGENT_SSL_VERIFY` | `True` | Verify TLS (set `False` for self-signed homelab certs) |
| `AUTHTOOL` | `True` | Register the authentication tool set |
| `RESOURCETOOL` | `True` | Register the resource (document/method) tool set |
| `HOST` / `PORT` / `TRANSPORT` | `0.0.0.0` / `8000` / `stdio` | HTTP transport binding |

The connector remains inactive when no `ERPNEXT_URL` / credentials are supplied.
A template lives in
[`.env.example`](https://github.com/Knuckles-Team/erpnext-agent/blob/main/.env.example)
— copy it to `.env` and fill in your site endpoint and token.

## Docker Compose

The repo ships
[`docker/mcp.compose.yml`](https://github.com/Knuckles-Team/erpnext-agent/blob/main/docker/mcp.compose.yml).
It reads a sibling `.env` and publishes the HTTP server on `:8000`:

```yaml
services:
  erpnext-agent-mcp:
    image: knucklessg1/erpnext-agent:latest
    container_name: erpnext-agent-mcp
    hostname: erpnext-agent-mcp
    restart: always
    env_file:
      - ../.env
    environment:
      - PYTHONUNBUFFERED=1
      - HOST=0.0.0.0
      - PORT=8000
      - TRANSPORT=streamable-http
      - ERPNEXT_URL
      - ERPNEXT_TOKEN
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
```

```bash
cp .env.example .env          # then edit ERPNEXT_URL / ERPNEXT_TOKEN
docker compose -f docker/mcp.compose.yml up -d
docker compose -f docker/mcp.compose.yml logs -f
```

## Behind a Caddy reverse proxy

Expose the HTTP server on a hostname with automatic TLS. Add to your `Caddyfile`:

```caddy
# Internal (self-signed) — homelab .arpa zone
erpnext-agent.arpa {
    tls internal
    reverse_proxy erpnext-agent-mcp:8000
}
```

```caddy
# Public — automatic Let's Encrypt
erpnext-agent.example.com {
    reverse_proxy erpnext-agent-mcp:8000
}
```

Reload Caddy:

```bash
docker compose -f services/caddy/compose.yml exec caddy caddy reload --config /etc/caddy/Caddyfile
```

## DNS with Technitium

Point the hostname at the host running Caddy. Via the Technitium API:

```bash
curl -s "http://technitium.arpa:5380/api/zones/records/add" \
  --data-urlencode "token=$TECHNITIUM_DNS_TOKEN" \
  --data-urlencode "domain=erpnext-agent.arpa" \
  --data-urlencode "zone=arpa" \
  --data-urlencode "type=A" \
  --data-urlencode "ipAddress=10.0.0.10" \
  --data-urlencode "ttl=3600"
```

…or add an **A record** `erpnext-agent.arpa → <caddy-host-ip>` in the Technitium web
console (`http://technitium.arpa:5380`). The ecosystem
[`technitium-dns-mcp`](https://knuckles-team.github.io/technitium-dns-mcp/) automates
this as a tool.

## Register with an MCP client

Add to your client's `mcp_config.json`:

```json
{
  "mcpServers": {
    "erpnext-agent": {
      "command": "uv",
      "args": ["run", "erpnext-mcp"],
      "env": {
        "ERPNEXT_URL": "https://your-erpnext:8000",
        "ERPNEXT_TOKEN": "your_api_key:your_api_secret"
      }
    }
  }
}
```

For a remote HTTP server, point the client at `http://erpnext-agent.arpa/mcp` instead.

## Agent server

In addition to the MCP server, `erpnext-agent` ships a Pydantic-AI **agent server**
(console script `erpnext-agent`). It connects to one or more MCP servers and exposes
a conversational agent over A2A:

```bash
# Run the agent server, wiring it to a running MCP endpoint
erpnext-agent --host 0.0.0.0 --port 8001 --mcp-url http://erpnext-agent-mcp:8000/mcp
```

The agent reads its toolset from an `mcp_config.json` (default: the bundled
`erpnext_agent/mcp_config.json`) or from the `--mcp-url` of an already-running MCP
server. A companion Compose service mirrors the MCP stack — publish the agent on its
own port (for example `:8001`) and set `MCP_URL` to the MCP server it should call:

```yaml
services:
  erpnext-agent:
    image: knucklessg1/erpnext-agent:latest
    container_name: erpnext-agent
    hostname: erpnext-agent
    restart: always
    entrypoint: ["erpnext-agent"]
    env_file:
      - ../.env
    environment:
      - PYTHONUNBUFFERED=1
      - HOST=0.0.0.0
      - PORT=8001
      - MCP_URL=http://erpnext-agent-mcp:8000/mcp
    ports:
      - "8001:8001"
    depends_on:
      - erpnext-agent-mcp
```

Provision an LLM provider for the agent through the standard `agent-utilities`
environment variables (provider/model selection via `--provider` / `--model-id`).
