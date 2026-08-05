---
title: Actian Zen
description: Connect MCP clients to Actian Zen for database exploration and read-only SQL queries.
---

# Actian MCP Server for Zen

Connect the MCP-compatible client to Actian Zen using the Actian MCP Server. The server handles automatic Zen dialect translation, allowing you to explore schema metadata, execute read-only SQL queries, and perform ORM operations through a standard interface.

## Capabilities

The Actian MCP Server for Zen supports the following operations:

| Action | Description |
|--------|-------------|
| **Run SQL queries** | Execute read-only SQL with automatic translation to Zen dialect. |
| **List tables and views** | Discover available objects and inspect their structures.|
| **ORM operations** | Query data using `JOIN`, `WHERE`, `ORDER BY`, and `LIMIT` clauses. |
| **Blob and file data** | List and download blob or file data stored in the database. |
| **Server management** | Query server capabilities, list DSNs, and release locks.|
| **Schema metadata** | View the database schema as a structured resource. |



## Prerequisites

Before starting the server, ensure the following requirements are met:

- **Container Engine:** Docker installed and running on the host machine.
- **Actian Zen Instance:** A running instance that the container can reach.
- **Credentials (Optional):** Required if the Zen database uses authentication.
- **OIDC provider (Optional):** Required if you are using OAuth authentication.


## Configuration

You can configure the MCP Server for Zen using a `conf.json` file. Mount this file into the container at `/app/conf.json`. Choose one of the two connection formats below based on the security requirements (credentials).

### Create the configuration file

**DSN connection (no credentials)**

Use this format when the built-in is `odbc.ini` and DSN is sufficient for requirements:

```json
{
  "database": "demodata",
  "conn_string": "DSN=demodata",
  "host": "0.0.0.0",
  "port": 8000
}
```

**Full driver connection (with credentials)**

Use this format when the database requires authentication. This bypasses the container's built-in `odbc.ini` and connects directly to the Zen engine.

```json
{
  "database": "demodata",
  "conn_string": "Driver=/opt/actianzen/lib64/libodbcci.so;ServerName=host.docker.internal:1583;DBQ=DEMODATA;UID=myuser;PWD=mypassword",
  "host": "0.0.0.0",
  "port": 8000
}
```

### Configuration reference

**Required fields**

| Field | Type | Description |
|-------|------|-------------|
| `conn_string` | `string` | ODBC connection string. Use `DSN=<name>` for the built-in DSN, or a full driver string with `UID` and `PWD` for authenticated connections. |
| `host` | `string` | Bind address for the MCP server inside the container. Set this to `0.0.0.0` so the server is reachable from outside the container.|
| `port` | `integer` | Port the MCP server listens on. This must match the port exposed by Docker (default `8000`). |

**Optional fields**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `database` | `string` | — | Logical database name used for display purposes. |
| `max_rows` | `integer` | `1000` | Maximum number of rows returned per query response. Default is `1000`. |
--8<-- "conf/common-optional-fields.md"

!!! note "OAuth and user impersonation"
    Actian Zen does not support `SET SESSION AUTHORIZATION`. If you use OAuth, set `user_impersonation: false` in the `oauth` block. The server logs the authenticated user but does not enforce it at the database level.


## Start the server

With `conf.json` ready, start the container and mount the configuration file as a
read-only volume:

```bash
docker run -d \
    --name=actian-mcp \
    -p 8000:8000 \
    --add-host=host.docker.internal:host-gateway \
    -v $(pwd)/conf.json:/app/conf.json:ro \
    actian/zen-mcp-server:1.1.0
```

!!! note "Container networking"
    `-p 8000:8000` exposes the server port on the host. `--add-host=host.docker.internal:host-gateway` allows the container to reach services on the host machine (such as the Zen engine on port 1583). Docker Desktop on Windows and macOS resolves `host.docker.internal` automatically; Linux requires the `--add-host` flag.

--8<-- "docker/mount-path-note.md"
--8<-- "conf/protection-note.md"

## Verify the connection

--8<-- "verify-connection.md"

## Next steps

<div class="grid cards" markdown>

- :material-connection: **[Connect a client](../mcp-clients/index.md)**  
  Point Claude Desktop, Cursor, GitHub Copilot, Codex, or fast-agent at the server
  endpoint.

- :material-tools: **[Tools](tools/index.md)**  
  Learn more about the SQL, ORM, and blob tools exposed by the Zen server.

- :material-folder-open: **[Resources](resources/index.md)**  
  Explore the resource types available through the server.

- :material-message-text: **[Prompts](prompts/index.md)**  
  Use the built-in prompt templates for common workflows.

- :material-puzzle: **[Extensions](../extensions/index.md)**  
  Add your own tools to the server with a Python extension.

</div>
