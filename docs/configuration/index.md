---
title: Configuration
description: Configure the Actian MCP Server for your environment — transports, plugins, authentication, and multi-tenancy.
---

# Configuration

The Actian MCP Server is configured via a JSON configuration file. By default it looks for `conf.json` in the working directory.

---

## Configuration File

```json
{
  "server": {
    "name": "actian-mcp-server",
    "version": "1.0.0",
    "transport": "stdio"
  },
  "plugins": [
    "actian_mcp_server.zen.plugin.ZenPlugin",
    "actian_mcp_server.analytics_engine.plugin.AnalyticsEnginePlugin"
  ],
  "oauth": {
    "FASTMCP_SERVER_AUTH_CONFIG_URL": "https://your-auth-server/.well-known/openid-configuration",
    "FASTMCP_SERVER_AUTH_CLIENT_ID": "your-client-id",
    "FASTMCP_SERVER_AUTH_CLIENT_SECRET": "your-client-secret",
    "FASTMCP_SERVER_AUTH_BASE_URL": "http://127.0.0.1:8000",
    "user_impersonation": true
  },
  "multitenancy": {
    "enabled": false
  },
  "read_only": false,
  "log_level": "INFO"
}
```

---

## Server Options

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `server.name` | string | `"actian-mcp-server"` | Server name reported to clients |
| `server.version` | string | `"1.0.0"` | Server version |
| `server.transport` | string | `"stdio"` | Transport mode: `stdio` or `sse` |
| `read_only` | boolean | `false` | Restrict all plugins to read-only operations |
| `log_level` | string | `"INFO"` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

---

## Transport Modes

### stdio (default)

Best for IDE integrations (Cursor, VS Code, Claude Desktop). The client launches the server as a subprocess.

```json
{ "server": { "transport": "stdio" } }
```

### SSE (Server-Sent Events)

Best for web-based or remote MCP clients.

```json
{
  "server": {
    "transport": "sse",
    "host": "0.0.0.0",
    "port": 8080
  }
}
```

---

## Plugin Configuration

List the fully-qualified class paths of plugins to load:

```json
{
  "plugins": [
    "actian_mcp_server.zen.plugin.ZenPlugin",
    "my_custom_plugin.plugin.MyPlugin"
  ]
}
```

Each plugin may accept its own configuration block. See each plugin's documentation for its specific options.

### Zen Plugin Options

```json
{
  "zen": {
    "dsn": "MyDatabase",
    "host": "localhost",
    "port": 1583,
    "username": "admin",
    "password": "secret"
  }
}
```

### Analytics Engine Plugin Options

```json
{
  "analytics_engine": {
    "host": "localhost",
    "port": 5439,
    "database": "mydb",
    "username": "admin",
    "password": "secret"
  }
}
```

---

## Authentication (OAuth 2.0)

The MCP server supports OAuth 2.0 / OIDC authentication for `sse`, `http`, and
`streamable-http` transports. When enabled, every request must carry a valid JWT.

Add an `oauth` block to your configuration file to enable authentication.
See the [Authentication](../authentication/index.md) section for the full
configuration reference and provider-specific setup guides (Auth0, Keycloak).

!!! note "Transport requirement"
    OAuth is not available with `stdio` transport.

---

## Multi-tenancy

When multi-tenancy is enabled, the server uses request context to route each call to the appropriate tenant's data source:

```json
{
  "multitenancy": {
    "enabled": true,
    "tenant_id_header": "X-Tenant-ID"
  }
}
```

---

## Environment Variables

Sensitive values can be provided via environment variables instead of the config file:

| Variable | Overrides |
|----------|-----------|
| `MCP_ZEN_DSN` | `zen.dsn` |
| `MCP_ZEN_PASSWORD` | `zen.password` |
| `MCP_AE_PASSWORD` | `analytics_engine.password` |
| `FASTMCP_SERVER_AUTH_CONFIG_URL` | `oauth.FASTMCP_SERVER_AUTH_CONFIG_URL` |
