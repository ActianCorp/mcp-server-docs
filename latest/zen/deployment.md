---
title: Deployment Scenarios
description: Where the Zen engine, the Actian MCP Server container and the agents sit — laptop, containers, remote engine, cloud — and which settings each layout needs.
---

# Deployment Scenarios

Three pieces take part: the agent (Claude Desktop, an IDE, a script), the MCP server container, and the Zen engine. Each can sit on a laptop, in a container, or on a cloud machine. Every setting answers one of three questions:

1. **How does the container find Zen?** The connection string, plus a Docker network flag.
2. **How do agents reach the container?** `host`, `port`, `-p`, and TLS.
3. **Who may do what?** `query_mode`, [read-only personas](multi-target.md#read-only-personas), [tokens and scopes](authentication/index.md#resource-server-mode).

## Finding Zen

The container talks to Zen over TCP like any remote Zen client. The only question is what name or address reaches the engine *from inside the container*; that is what `ServerName=` in `conn_string` (or `host` in a target entry) must say.

| Zen engine is... | `ServerName=` | `docker run` needs | Notes |
|------------------|---------------|--------------------|-------|
| Installed on the same Windows or macOS machine | `host.docker.internal:1583` | `--add-host=host.docker.internal:host-gateway` (Docker Desktop resolves the name anyway) | Zen must listen on 1583, its default. |
| Installed on the same Linux machine | `host.docker.internal:1583` | `--add-host=host.docker.internal:host-gateway` | Linux Docker has no built-in `host.docker.internal`; the flag creates it. |
| In another container | `<alias>:1583`, for example `zen16:1583` | `--network <name>` on both containers; start the engine with `--network-alias <alias>` | The engine port needs no `-p`. |
| On another machine or a cloud VM | `<dns-name-or-ip>:1583` | nothing | Port 1583 must be open from the MCP host to the Zen host. With Zen security on, add `UID=` and `PWD=`. |

!!! warning "Not `localhost`, and not a bare DSN"
    From inside a container `localhost` is the container itself, and the Zen client for Linux resolves the name to `::1`; both fail with `SQL Connection Manager is not running at the specified port number (10065)`. The DSN bundled in the image is not honored for a remote connect either — the client falls back to `127.0.0.1`. Always give an explicit `ServerName=<name>:1583` in `conn_string`.

## Letting Agents In

`host` and `port` in `conf.json` are the address *inside* the container. With `-p`, `host` must be `0.0.0.0`; who may connect is decided by the left side of `-p` and by the firewall, not by `host`.

| Agents connect from... | `conf.json` | `docker run` | TLS | Authentication |
|------------------------|-------------|--------------|-----|----------------|
| This machine only | `"host": "0.0.0.0"`, `"port": 8000` | `-p 127.0.0.1:8000:8000` | not needed | not needed |
| Other machines on a private network | same | `-p 8000:8000` | advised | advised — without it, anyone who can reach the port queries the database as the connection-string login |
| The internet or a cloud network | same, plus `ssl_certfile` and `ssl_keyfile` | `-p 8000:8000`, the certificate and key mounted at `/app/server.crt` and `/app/server.key` | mandatory | mandatory — [resource-server mode](authentication/index.md#resource-server-mode) |

!!! note "The rule the server enforces"
    With authentication on and `host` other than `localhost` (so also `0.0.0.0`), both TLS files must be present or the server refuses to start: `ssl_certfile and ssl_keyfile are required for OAuth on non-localhost hosts`. The paths in `conf.json` are the in-container paths `/app/server.crt` and `/app/server.key`; see [HTTPS and TLS](authentication/index.md#secure-remote-deployments-with-https-and-tls).

The URL an agent uses is `http://<mcp-host>:8000/mcp` for a single-database server and `http://<mcp-host>:8000/mcp/{host}/{instance}/{database}/mcp` per target when the server [serves several](multi-target.md). With TLS the scheme is `https`.

## Scenarios

| | Zen engine | MCP container | Agents | Authentication | Typical use |
|---|-----------|---------------|--------|----------------|-------------|
| A | installed on the laptop | Docker Desktop on the laptop | the same laptop | none | first look with Claude Desktop or an IDE |
| B | container on the laptop | container on the laptop | the same laptop | none | development and tests |
| C | container on the laptop | container, several URLs | the same laptop | none (`allow_unscoped_reads`) | trying multi-target |
| D | one or more engines | server on a VM in a private network | the office network | identity provider, TLS | a team deployment |

### A. Zen on the Laptop, Server in Docker Desktop

```json title="conf.json"
{
  "database": "DEMODATA",
  "conn_string": "Driver=/opt/actianzen/lib64/libodbcci.so;ServerName=host.docker.internal:1583;DBQ=DEMODATA",
  "query_mode": "read-only",
  "host": "0.0.0.0",
  "port": 8000
}
```

```bash
docker run -d --name zen-mcp -p 127.0.0.1:8000:8000 \
  --add-host=host.docker.internal:host-gateway \
  -v $(pwd)/conf.json:/app/conf.json:ro \
  actian/zen-mcp-server:1.1.0
```

Agent URL: `http://localhost:8000/mcp`. If the log shows error `10065`, the container cannot reach the engine on the laptop; check that Zen listens on 1583 and that the host firewall lets Docker's network through.

### B. Engine and Server in Containers

```bash
docker network create zentest
docker run -d --name zen16 --network zentest --network-alias zen16 <zen-engine-image>
docker run -d --name zen-mcp --network zentest -p 8000:8000 \
  -v $(pwd)/conf.json:/app/conf.json:ro \
  actian/zen-mcp-server:1.1.0
```

The only change from A: `--network zentest` instead of `--add-host`, and `ServerName=zen16:1583` in `conn_string`, because the engine now lives in a container named `zen16` on the network `zentest`.

### C. Several URLs Without Authentication

The configuration from [Multiple Databases](multi-target.md#configuration), with `allow_unscoped_reads: true`, and a folder for hot add and remove:

```bash
mkdir targets.d
docker run -d --name zen-mcp --network zentest -p 8000:8000 \
  -v $(pwd)/conf.json:/app/conf.json:ro \
  -v $(pwd)/targets.d:/app/targets.d \
  actian/zen-mcp-server:1.1.0
```

Then the checks in [Verifying a setup](multi-target.md#verifying-a-setup).

### D. A Team Deployment with an Identity Provider

The configuration from C, minus `allow_unscoped_reads`, plus the [resource-server block](authentication/index.md#resource-server-mode) and TLS:

```json
{
  "auth_mode": "resource-server",
  "oauth": {
    "FASTMCP_SERVER_AUTH_CONFIG_URL": "https://<idp>/realms/<realm>/.well-known/openid-configuration",
    "FASTMCP_SERVER_AUTH_AUDIENCE": "<audience>",
    "FASTMCP_SERVER_AUTH_BASE_URL": "https://<mcp-host>:8000",
    "user_impersonation": false
  },
  "ssl_certfile": "/app/server.crt",
  "ssl_keyfile": "/app/server.key"
}
```

```bash
docker run -d --name zen-mcp -p 8000:8000 \
  -v /path/to/conf.json:/app/conf.json:ro \
  -v /path/to/server.crt:/app/server.crt:ro \
  -v /path/to/server.key:/app/server.key:ro \
  actian/zen-mcp-server:1.1.0
```

Each target entry carries the Zen login for its engine; `conf.json` therefore holds passwords and should be readable by nobody else on the host. Open 1583 from the MCP host to each engine, and 8000 to the agents' network only.

## When Something Goes Wrong

| You see | It means | Do |
|---------|----------|----|
| `SQL Connection Manager is not running at the specified port number (10065)` | The container cannot reach Zen at `ServerName`: wrong name, wrong network, firewall, or `localhost` from a Linux container. | Check the [Finding Zen](#finding-zen) table. Never `localhost` from a container. |
| `ssl_certfile and ssl_keyfile are required for OAuth on non-localhost hosts` | Authentication is on and `host` is not `localhost`. | Mount a certificate and key, see [HTTPS and TLS](authentication/index.md#secure-remote-deployments-with-https-and-tls). |
| `ssl_certfile path does not exist or is empty` | The mount did not land, or the paths in `conf.json` differ from the mount. | Mount at exactly `/app/server.crt` and `/app/server.key`. |
| `401` and `issuer mismatch` in the log | The token's issuer is not the address in `FASTMCP_SERVER_AUTH_CONFIG_URL`. | The container and the token requests must name the identity provider the same way; a Keycloak started with `KC_HOSTNAME` pins the issuer. |
| `404` on a target URL that exists | The token has no `actian:...:read` grant for that exact target, or the path has a typo. The server gives the same `404` on purpose. | Grant the scope at the identity provider; compare the path with `list_accessible_targets`. |
| `Access denied to a READ-ONLY data source` | The URL's persona is in `zen_readonly_personas`, or the server is `read-only`. | Use a read-write persona, or set `query_mode` to `read-write`. This is the expected result of a read-only check. |
| `N targets are configured, but per-target scope enforcement ... is not active` at start | Several targets need either authentication or `allow_unscoped_reads: true`. | Add `auth_mode: "resource-server"`, or the escape hatch for a test setup. |

`docker logs <container>` shows the start-up lines, every [call log](index.md#call-log) record, and the refusals above.
