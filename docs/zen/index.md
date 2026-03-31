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

Create a file such as `conf.json` with the following structure:

```json
{
    "database": "demodata",
    "conn_string": "DSN=demodata",
    "max_rows": 1000
}
```

Use these fields as follows:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `database` | `str` | No | Logical database name, used for display purposes. |
| `conn_string` | `str` | Yes | ODBC connection string. Typically `DSN=<dsn_name>`. |
| `max_rows` | `int` | No | Maximum number of rows returned for a single query response. Defaults to `1000`. |
| `oauth` | `object` | No | OAuth configuration block for protected deployments. See [Authentication](../authentication/index.md) for details. |

!!! note
    Zen does not support `SET SESSION AUTHORIZATION`. When using OAuth, set `user_impersonation: false` in the `oauth` block. The authenticated user is logged but not enforced at the database level.

## Starting the server

The Zen MCP Server is deployed as a container image.

```bash
docker run -d \
    -v $(pwd)/conf.json:/app/conf.json:ro \
    actian/zen-mcp-server:1.0.0
```

!!! note "Container networking"
    When the container connects to a Zen engine on the host machine, you must provide the host's reachable IP address (not `localhost`). On Windows with Podman/WSL, the `start-zen-mcp.ps1` helper script automates IP detection and container startup.

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
