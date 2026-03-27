---
title: Actian Zen
description: Use the Actian MCP Server to connect MCP clients to Actian Zen.
---

# Actian Zen

This page explains how to use the **Actian MCP Server** with **Actian Zen**.

When configured for Zen, the server gives an MCP-compatible client a rich set of tools for database exploration, query execution, ORM-based CRUD, schema management, blob/file handling, and transaction control.

## What you can do

With the Zen server, AI clients can:

- Run **read-only or read-write SQL queries** with automatic Zen dialect translation.
- List available tables and inspect their structure.
- Perform **ORM operations** with JOINs (up to 3 tables), WHERE, ORDER BY, and LIMIT.
- Execute **DDL operations**: create/drop tables, columns, indexes, views, procedures, functions, and triggers.
- Manage **blob/file data**: upload, download, list, and delete.
- Control **transactions**: BEGIN, COMMIT, and ROLLBACK with timeout.
- List DSNs, query server capabilities, and release locks.
- Read database schema metadata as a resource.

In **full mode** (default), 9 tools are registered. In **read-only mode** (`readonly=true`), 6 read-only tools are available and write operations are blocked at both the tool and database level.

## Configuration

The Zen MCP Server reads its configuration from a JSON file named `zen_config.json`. Three formats are supported:

### Minimal (DSN only)

```json
{
	"conn_string": "DSN=demodata"
}
```

### Standard

```json
{
	"database": "demodata",
	"readonly": false,
	"transport": "stdio",
	"max_rows": 1000,
	"conn_string": "DSN=demodata"
}
```

### Full (with OAuth and network settings)

```json
{
	"database": "demodata",
	"readonly": false,
	"transport": "http",
	"max_rows": 1000,
	"conn_string": "DSN=demodata",
	"host": "0.0.0.0",
	"port": "8000",
	"oauth": {
		"FASTMCP_SERVER_AUTH_CONFIG_URL": "<oidc_discovery_url>",
		"FASTMCP_SERVER_AUTH_CLIENT_ID": "<client_id>",
		"FASTMCP_SERVER_AUTH_CLIENT_SECRET": "<client_secret>",
		"FASTMCP_SERVER_AUTH_BASE_URL": "<server_base_url>",
		"FASTMCP_SERVER_AUTH_AUDIENCE": "<audience>",
		"FASTMCP_SERVER_AUTH_SCOPE": "<scopes>",
		"user_impersonation": false
	}
}
```

Use these fields as follows:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `database` | `str` | No | Logical database name, used for display purposes. |
| `readonly` | `bool` | No | When `true`, only 6 read-only tools are registered. Defaults to `false`. |
| `transport` | `str` | No | MCP transport mode: `stdio`, `http`, or `sse`. Defaults to `stdio`. |
| `max_rows` | `int` | No | Maximum number of rows returned for a single query response. Defaults to `1000`. |
| `conn_string` | `str` | Yes | ODBC connection string. Typically `DSN=<dsn_name>`. |
| `host` | `str` | No | Host address that the MCP Server listens on. Required for `http` and `sse` transports. |
| `port` | `str` | No | Port that the MCP Server listens on. Required for `http` and `sse` transports. |
| `oauth` | `object` | No | OAuth configuration block for protected MCP server deployments. See [The `oauth` configuration block](../authentication/index.md#the-oauth-configuration-block) for the required fields. |

!!! note
    Zen does not support `SET SESSION AUTHORIZATION`. When using OAuth, set `user_impersonation: false` in the `oauth` block. The authenticated user is logged but not enforced at the database level.

## Starting the server

### Local (stdio)

```bash
uv run actian-mcp-server --dbms=zen --conf-file=src/zen/zen_config.json
```

Or with auto-discovery (Windows only, uses the first Zen DSN found in the ODBC registry):

```bash
uv run actian-mcp-server --dbms=zen
```

### Container (Podman/Docker)

```bash
podman run -d \
	-v $(pwd)/zen_config.json:/app/conf.json:ro \
	actian/zen-mcp-server:1.0.0
```

!!! note "Container networking"
    When running the MCP Server in a container that connects to a Zen engine on the host, you must use the host's reachable IP address (not `localhost`). On Windows with WSL, use the WSL IP address. The `start-zen-mcp.ps1` helper script automates this by detecting the WSL IP and passing it to the container.

## Next steps

- [Tools](tools/index.md) — Learn about Zen tools
- [Resources](resources/index.md) — Learn about Zen resources
- [Prompts](prompts/index.md) — Learn about Zen prompts
- [Testing](testing/index.md) — Test coverage and results
