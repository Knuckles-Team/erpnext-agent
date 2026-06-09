# Backing Platform — ERPNext / Frappe

`erpnext-agent` is a **client** of an ERPNext / Frappe site. This page provides a
Docker recipe for deploying one locally to serve as the target of `ERPNEXT_URL`. For
production topologies, follow the upstream
[Frappe Docker documentation](https://github.com/frappe/frappe_docker).

!!! note "Backing-system recipe"
    Each connector in the ecosystem follows the same convention — a
    `docs/platform.md` recipe for the system it integrates with, accompanied by a
    sample Compose stack that mirrors the ecosystem
    [`services/`](https://github.com/Knuckles-Team) deployment declarations. Systems
    offered only as a managed service have no local recipe.

## Single-node deployment (Compose)

ERPNext publishes the `frappe/erpnext` image, backed by MariaDB and Redis. The
following stack runs one site on `:8000`:

```yaml
# docker/erpnext-platform.compose.yml
services:
  erpnext:
    image: frappe/erpnext:v15.20.0
    container_name: erpnext
    restart: unless-stopped
    environment:
      - MARIADB_HOST=erpnext-db
      - REDIS_CACHE=redis://erpnext-redis:6379/0
      - REDIS_QUEUE=redis://erpnext-redis:6379/1
      - REDIS_SOCKETIO=redis://erpnext-redis:6379/2
    ports:
      - "8000:8000"            # Frappe site (HTTP)
    volumes:
      - erpnext_sites:/home/frappe/frappe-bench/sites
    depends_on:
      - erpnext-db
      - erpnext-redis

  erpnext-db:
    image: mariadb:10.6
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
    restart: unless-stopped
    environment:
      - MYSQL_ROOT_PASSWORD=change-me-root
      - MYSQL_DATABASE=erpnext
      - MYSQL_USER=erpnext
      - MYSQL_PASSWORD=change-me
    volumes:
      - erpnext_db:/var/lib/mysql

  erpnext-redis:
    image: redis:7-alpine
    restart: unless-stopped

volumes:
  erpnext_sites:
  erpnext_db:
```

```bash
docker compose -f docker/erpnext-platform.compose.yml up -d

# Wait for the site to answer (the version endpoint is unauthenticated)
curl -s http://localhost:8000/api/method/version
```

After the site is created, generate an API key/secret pair from
**Settings → My Settings → API Access** in the ERPNext UI; the connector consumes it
as `api_key:api_secret`.

## Connect erpnext-agent

```bash
export ERPNEXT_URL=http://localhost:8000
export ERPNEXT_TOKEN=your_api_key:your_api_secret
export ERPNEXT_AGENT_SSL_VERIFY=False          # if the site uses a self-signed cert

erpnext-mcp --transport streamable-http --host 0.0.0.0 --port 8000
```

## Combined deployment

A combined stack places the ERPNext site and the MCP server on one Docker network, so
the server reaches ERPNext by container name:

```yaml
# docker/stack.compose.yml
services:
  erpnext:
    image: frappe/erpnext:v15.20.0
    hostname: erpnext
    environment:
      - MARIADB_HOST=erpnext-db
      - REDIS_CACHE=redis://erpnext-redis:6379/0
      - REDIS_QUEUE=redis://erpnext-redis:6379/1
      - REDIS_SOCKETIO=redis://erpnext-redis:6379/2
    volumes: ["erpnext_sites:/home/frappe/frappe-bench/sites"]
    depends_on: [erpnext-db, erpnext-redis]

  erpnext-db:
    image: mariadb:10.6
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
    environment:
      - MYSQL_ROOT_PASSWORD=change-me-root
      - MYSQL_DATABASE=erpnext
      - MYSQL_USER=erpnext
      - MYSQL_PASSWORD=change-me
    volumes: ["erpnext_db:/var/lib/mysql"]

  erpnext-redis:
    image: redis:7-alpine

  erpnext-agent-mcp:
    image: knucklessg1/erpnext-agent:latest
    depends_on: [erpnext]
    environment:
      - ERPNEXT_URL=http://erpnext:8000
      - ERPNEXT_TOKEN=your_api_key:your_api_secret
      - TRANSPORT=streamable-http
      - HOST=0.0.0.0
      - PORT=8000
    ports: ["8000:8000"]

volumes:
  erpnext_sites:
  erpnext_db:
```

```bash
docker compose -f docker/stack.compose.yml up -d
```

Once the site is reachable, the [MCP tools](usage.md#as-an-mcp-server) and the
[`Api` client](usage.md#as-a-python-api) operate against any ERPNext DocType and
whitelisted RPC method.
