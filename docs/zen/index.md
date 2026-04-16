---
title: Actian Zen
description: Use the Actian MCP Server to connect MCP clients to Actian Zen.
---

# Actian Zen

This page explains how to use the **Actian MCP Server** with **Actian Zen**.

When configured for Zen, the server gives an MCP-compatible client a set of tools for database exploration and read-only query execution through a standard MCP interface.

## What you can do

With the Zen server, AI clients can:

- Run **read-only SQL queries** with automatic Zen dialect translation.
- List available tables and inspect their structure.
- Perform **ORM operations** with JOINs, WHERE, ORDER BY, GROUP BY, and LIMIT.
- List and download **blob/file data**.
- Query server capabilities, list DSNs, and release locks.
- Read database schema metadata as a resource.

## Configuration

The container image is pre-configured to connect to a Zen database. The main user-provided input is a JSON configuration file that is mounted into the container.

Create a file such as `conf.json` and mount it into the container. Two connection formats are supported:

**Using the built-in DSN (no credentials):**

```json
{
    "database": "demodata",
    "conn_string": "DSN=demodata",
    "host": "0.0.0.0",
    "port": 8000
}
```

**Using a full driver connection string (with credentials):**

```json
{
    "database": "demodata",
    "conn_string": "Driver=/opt/actianzen/lib64/libodbcci.so;ServerName=host.docker.internal:1583;DBQ=DEMODATA;UID=myuser;PWD=mypassword",
    "host": "0.0.0.0",
    "port": 8000
}
```

The full driver string connects directly to the Zen engine without relying on the container's built-in `odbc.ini`. Use this format when the database requires authentication.

Use these fields as follows:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conn_string` | `str` | Yes | ODBC connection string. Use `DSN=<name>` for the built-in DSN, or a full driver string with `UID` and `PWD` for authenticated connections. |
| `host` | `str` | Yes | Bind address for the MCP server inside the container. Must be `0.0.0.0` for the server to be reachable from outside the container. |
| `port` | `int` | Yes | Port the MCP server listens on. Must match the port exposed by Docker (typically `8000`). |
| `database` | `str` | No | Logical database name, used for display purposes. |
| `max_rows` | `int` | No | Maximum number of rows returned for a single query response. Defaults to `1000`. |
| `oauth` | `object` | No | OAuth configuration block for protected deployments. See [Authentication](../authentication/index.md) for details. |

!!! note
    Zen does not support `SET SESSION AUTHORIZATION`. When using OAuth, set `user_impersonation: false` in the `oauth` block. The authenticated user is logged but not enforced at the database level.

## Starting the server

The Zen MCP Server is deployed as a container image.

```bash
docker run -d \
    -p 8000:8000 \
    --add-host=host.docker.internal:host-gateway \
    -v $(pwd)/conf.json:/app/conf.json:ro \
    actian/zen-mcp-server:latest
```

!!! note "Container networking"
    `-p 8000:8000` exposes the server port on the host. `--add-host=host.docker.internal:host-gateway` allows the container to reach services on the host machine (such as the Zen engine on port 1583). Docker Desktop on Windows and macOS resolves `host.docker.internal` automatically; Linux requires the `--add-host` flag. On Windows, the `start-zen-mcp.ps1` helper script automates container startup.

After the container starts, connect your MCP client to the exposed server endpoint using the transport configured for your deployment.

## What users should expect

Once the container is running and connected to Zen, an MCP client can discover the available server capabilities automatically.

In practice, this means a user can ask the client to:

- Inspect database structure before writing a query.
- Run a read-only query and summarize the results.
- Look up details for a specific table.
- Explore relationships between tables.

This keeps Zen access available through a consistent MCP workflow while the server manages the database connection, SQL dialect translation, and response formatting.

## Next steps

- [Tools](tools/index.md) — Learn about Zen tools
- [Resources](resources/index.md) — Learn about Zen resources
- [Prompts](prompts/index.md) — Learn about Zen prompts
