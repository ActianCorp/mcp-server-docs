---
title: Actian Zen
description: Connect MCP clients to Actian Zen for database exploration and read-only SQL queries.
---

# Actian Zen

Connect your MCP-compatible client to **Actian Zen** using the Actian MCP Server. Once configured, clients can explore schema metadata, execute read-only SQL queries, and perform ORM operations through a standard MCP interface — with automatic Zen dialect translation handled by the server.


## Overview

### Capabilities

| Action | Description |
|--------|-------------|
| **Run SQL queries** | Execute read-only SQL with automatic Zen dialect translation. |
| **List tables and views** | Discover available objects and inspect their structure. |
| **ORM operations** | Query with JOINs, WHERE, ORDER BY, GROUP BY, and LIMIT clauses. |
| **Blob and file data** | List and download blob or file data stored in the database. |
| **Server management** | Query server capabilities, list DSNs, and release locks. |
| **Schema metadata** | Read database schema as a structured resource. |



## Prerequisites

- Docker installed and running.
- A running Actian Zen instance reachable from the container.
- (Optional) Database credentials if your Zen database requires authentication.
- (Optional) An OIDC provider if using OAuth authentication.



## Configuration

The Zen MCP Server is configured via a single `JSON` file mounted into the container at `/app/conf.json`. Two connection formats are supported depending on whether your database requires credentials.

### Connection Formats

**DSN Connection (No Credentials)**

Use this format when the built-in `odbc.ini` DSN is sufficient.

```json
{
  "database": "demodata",
  "conn_string": "DSN=demodata",
  "host": "0.0.0.0",
  "port": 8000
}
```

**Full Driver Connection (With Credentials)**

Use this format when the database requires authentication. This bypasses the container's built-in `odbc.ini` and connects directly to the Zen engine.

```json
{
  "database": "demodata",
  "conn_string": "Driver=/opt/actianzen/lib64/libodbcci.so;ServerName=host.docker.internal:1583;DBQ=DEMODATA;UID=myuser;PWD=mypassword",
  "host": "0.0.0.0",
  "port": 8000
}
```

### Configuration Reference

**Required Fields**

| Field | Type | Description |
|-------|------|-------------|
| `conn_string` | `string` | ODBC connection string. Use `DSN=<name>` for the built-in DSN, or a full driver string with `UID` and `PWD` for authenticated connections. |
| `host` | `string` | Bind address for the MCP server inside the container. Must be `0.0.0.0` for the server to be reachable from outside the container. |
| `port` | `integer` | Port the MCP server listens on. Must match the port exposed by Docker (typically `8000`). |

**Optional Fields**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `database` | `string` | — | Logical database name used for display purposes. |
| `max_rows` | `integer` | `1000` | Maximum number of rows returned per query response. |
| `oauth` | `object` | — | OAuth configuration block for protected deployments. See [Authentication](../authentication/index.md). |

!!! note "OAuth and user impersonation"
    Zen does not support `SET SESSION AUTHORIZATION`. When using OAuth, set `user_impersonation: false` in the `oauth` block. The authenticated user is logged but not enforced at the database level.

---

## Start the Server

With your `conf.json` ready, start the container and mount the configuration file:

```bash
docker run -d \
  -p 8000:8000 \
  --add-host=host.docker.internal:host-gateway \
  -v $(pwd)/conf.json:/app/conf.json:ro \
  actian/zen-mcp-server:latest
```

!!! note "Container networking"
    `-p 8000:8000` exposes the server port on the host. `--add-host=host.docker.internal:host-gateway` allows the container to reach services on the host machine (such as the Zen engine on port 1583). Docker Desktop on Windows and macOS resolves `host.docker.internal` automatically; Linux requires the `--add-host` flag. On Windows, the `start-zen-mcp.ps1` helper script automates container startup.

Once the container is running, connect your MCP client to the exposed server endpoint using the host and port from your configuration.

---

## Usage

After connecting, your MCP client automatically discovers the server's capabilities. Common tasks include:

- **Inspect before querying** — List tables and review structure before writing SQL.
- **Run a query** — Execute a read-only SQL statement and receive formatted results.
- **Explore relationships** — Traverse foreign keys and related tables using ORM operations.
- **Summarize results** — Ask the client to interpret or summarize query output.

---

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](tools/index.md)**
  Learn about the SQL, ORM, and blob tools exposed by the Zen server.

- :material-folder-open: **[Resources](resources/index.md)**
  Explore the resource types available through the server.

- :material-message-text: **[Prompts](prompts/index.md)**
  Review the built-in prompt templates for common workflows.

</div>
