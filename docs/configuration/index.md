---
title: Zen Configuration
description: Configure the Zen MCP Server — database connection, transports, readonly mode, OAuth, and CLI overrides.
---

# Zen Configuration

The Zen plugin reads its settings from a JSON configuration file, environment variables, and CLI arguments. When the same option appears in multiple places, the highest-priority source wins:

**CLI arguments > environment variables > config file > auto-discovery**

---

## zen_config.json

The server looks for `zen_config.json` in the working directory by default. Override the path with `--conf-file`.

### Full example (all keys)

```json
{
    "database": "DEMODATA",
    "readonly": true,
    "transport": "streamable-http",
    "max_rows": 1000,
    "host": "0.0.0.0",
    "port": 8000,
    "ssl_certfile": "/path/to/server.crt",
    "ssl_keyfile": "/path/to/server.key",
    "oauth": {
        "FASTMCP_SERVER_AUTH_CONFIG_URL": "https://auth0.example.com/.well-known/openid-configuration",
        "FASTMCP_SERVER_AUTH_CLIENT_ID": "your-client-id",
        "FASTMCP_SERVER_AUTH_CLIENT_SECRET": "your-client-secret",
        "FASTMCP_SERVER_AUTH_BASE_URL": "https://your-server:8000",
        "FASTMCP_SERVER_AUTH_AUDIENCE": "your-audience",
        "FASTMCP_SERVER_AUTH_SCOPE": "openid email profile",
        "FASTMCP_SERVER_AUTH_REDIRECT_PATH": "/oauth/callback",
        "user_impersonation": false
    }
}
```

Most keys are optional. Minimal config needs only `database`.

### Simple format

Specify just the DSN name. The server connects via the system ODBC data source:

```json
{
  "database": "DEMODATA"
}
```

### Connection string format

Pass a full ODBC connection string:

```json
{
  "conn_string": "Driver={Pervasive ODBC Interface};ServerName=localhost;DBQ=DEMODATA;"
}
```

### Connection object format

Provide individual connection fields:

```json
{
  "connection": {
    "DSN": "DEMODATA",
    "uid": "admin",
    "pwd": "secret"
  }
}
```

---

## All Configuration Keys

Every key that the system reads from `zen_config.json`:

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `database` | string | *(auto-discover)* | DSN name or database path |
| `conn_string` | string | — | Full ODBC connection string (overrides `database`) |
| `connection` | object | — | Connection object with `type`, `dsn`, `uid`, `pwd` |
| `connection.type` | string | — | `"dsn"` or `"driver"` |
| `connection.dsn` | string | — | DSN name |
| `connection.uid` | string | — | Database username |
| `connection.pwd` | string | — | Database password |
| `readonly` | boolean | `true` | Restrict to 6 read-only tools |
| `transport` | string | `"stdio"` | `stdio`, `http`, `sse`, or `streamable-http` |
| `max_rows` | integer | `1000` | Maximum rows returned per query |
| `host` | string | `""` | Bind address for HTTP/SSE transports |
| `port` | integer | `8000` | Listen port for HTTP/SSE transports |
| `username` | string | — | DB username (non-Zen plugins, Zen uses DSN credentials) |
| `password` | string | — | DB password (non-Zen plugins, Zen uses DSN credentials) |
| `ssl_certfile` | string | — | Path to TLS certificate (HTTPS) |
| `ssl_keyfile` | string | — | Path to TLS private key (HTTPS) |
| `oauth` | object | `{}` | OAuth 2.0 configuration block (see below) |
| `oauth.FASTMCP_SERVER_AUTH_CONFIG_URL` | string | — | OIDC discovery URL |
| `oauth.FASTMCP_SERVER_AUTH_CLIENT_ID` | string | — | OAuth client ID |
| `oauth.FASTMCP_SERVER_AUTH_CLIENT_SECRET` | string | — | OAuth client secret |
| `oauth.FASTMCP_SERVER_AUTH_BASE_URL` | string | — | Server base URL for OAuth redirects |
| `oauth.FASTMCP_SERVER_AUTH_AUDIENCE` | string | — | Expected JWT audience |
| `oauth.FASTMCP_SERVER_AUTH_SCOPE` | string | — | Required OAuth scopes (space-separated) |
| `oauth.FASTMCP_SERVER_AUTH_REDIRECT_PATH` | string | — | Custom OAuth redirect path |
| `oauth.user_impersonation` | boolean | `true` | Forward JWT username to DB session. Must be `false` for Zen. |

`ssl_certfile` and `ssl_keyfile` must both be present or both absent. When set with OAuth, `FASTMCP_SERVER_AUTH_BASE_URL` must use `https://`. OAuth is silently skipped if `FASTMCP_SERVER_AUTH_CONFIG_URL` or `FASTMCP_SERVER_AUTH_CLIENT_ID` are absent.

---

## Transport Modes

### stdio (default)

Best for IDE integrations — Claude Desktop, Cursor, VS Code. The MCP client launches the server as a subprocess.

```json
{
  "transport": "stdio"
}
```

### streamable-http

HTTP transport on port 8000. Used for container deployments and remote access.

```json
{
  "transport": "streamable-http"
}
```

The server listens on `0.0.0.0:8000` by default.

### sse (Server-Sent Events)

Legacy HTTP transport. Same port as streamable-http.

```json
{
  "transport": "sse"
}
```

---

## Readonly Mode

When `readonly` is `true` (the default), the server registers **6 tools**:

- `execute_query`
- `list_tables`
- `describe_table`
- `orm_operation`
- `blob_operation`
- `database_manage`

When `readonly` is `false`, **3 additional write tools** become available:

- `ddl_operation`
- `batch_operation`
- `transaction`

In readonly mode, all write SQL is blocked at two layers: a Python SQL parser rejects non-SELECT statements, and the ODBC connection opens with `OPENMODE=1` (read-only at the engine level).

---

## CLI Arguments

| Argument | Description |
|----------|-------------|
| `--conf-file PATH` | Path to `zen_config.json` |
| `--dsn NAME` | Override the DSN (equivalent to `database` in config) |
| `--transport MODE` | Override transport: `stdio`, `streamable-http`, `sse` |
| `--readonly` | Force readonly mode |

Example:

```bash
uv run actian-mcp-server --dbms zen --dsn DEMODATA --transport streamable-http
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `ZEN_DSN` | DSN name — same as `database` in config |
| `ZEN_CONN_STRING` | Full ODBC connection string — same as `conn_string` in config |

Environment variables override config-file values but are overridden by CLI arguments.

---

## OAuth Configuration

To enable OAuth 2.0 JWT validation (typically for HTTP transports), add environment variables with the `FASTMCP_SERVER_AUTH_` prefix:

| Variable | Description |
|----------|-------------|
| `FASTMCP_SERVER_AUTH_ISSUER` | Token issuer URL (e.g. `https://your-idp.example.com/`) |
| `FASTMCP_SERVER_AUTH_AUDIENCE` | Expected audience claim |
| `FASTMCP_SERVER_AUTH_CLIENT_ID` | OAuth client ID |
| `FASTMCP_SERVER_AUTH_CLIENT_SECRET` | OAuth client secret |
| `FASTMCP_SERVER_AUTH_JWKS_URI` | JWKS endpoint for token verification |

**Zen-specific note:** Zen/PSQL does not support `SET SESSION AUTHORIZATION`, so `user_impersonation` must be disabled. The server extracts the username from the JWT (priority: `username` > `preferred_username` > email prefix > `sub`) for audit logging only — it cannot switch the database session identity.

---

## Container Deployment

When running inside a Podman container, configuration is passed via environment variables or a mounted config file. See the [Deployment](../deployment/index.md) page for container build and run instructions.
