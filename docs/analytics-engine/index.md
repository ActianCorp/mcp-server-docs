---
title: Actian Analytics Engine
description: Connect MCP clients to Actian Analytics Engine for schema exploration and SQL queries, with optional write support.
---

# Actian MCP Server for Analytics Engine

Connect the MCP-compatible client to the Actian Analytics Engine using the Actian MCP Server. This setup allows you to explore schema metadata and run SQL queries through a standard interface. Queries are read-only unless you enable write mode. The MCP Server for Analytics Engine bridges the gap between the MCP client and the Actian database. The server manages connection pooling, response formatting, and schema discovery automatically, allowing you to focus on the data.


## Capabilities

The Actian Analytics Engine MCP Server supports the following operations:

| Action | Description |
|--------|-------------|
| **Execute SQL queries** | Execute read-only SQL against the database |
| **List tables and views** | Discover available objects in the schema |
| **Inspect table structure** | Retrieve column definitions and types |
| **Read schema metadata** | Explore database-level metadata |
| **List functions and procedures** | View available user-defined functions and procedures |
| **Execute write queries** | Run `INSERT`, `UPDATE`, and `DELETE` statements. Off by default. Requires `query_mode` set to `read-write` |

!!! note "Write support is opt-in"
    The server permits only read queries unless you set `query_mode` to `read-write`. Each write then requires the `mcp:write` scope and human approval. For more information, see [Write support](../intro/write-support.md).


## Prerequisites

Before starting the server, ensure the following requirements are met:

- **Container Engine:** Docker installed and running on the host machine.
- **Database credentials:** Valid access for the Analytics Engine database.
- **Security files (optional):** TLS certificate and key files for secure deployments.
- **OIDC provider (optional):** Required if you are using OAuth authentication.


## Configuration

The server runs as a Docker container. To configure the server, mount the (`conf.json`) file to the container at `/app/conf.json`.

### Create the configuration file

Create a file named `conf.json` in your working directory using the following structure:

```json
{
  "driver": "<odbc_driver>",
  "server": "<database_host>",
  "database": "<database_name>",
  "max_connections": "<max_concurrent_connections>",
  "max_rows": "<max_rows_per_query_response>",
  "host": "<mcp_server_host>",
  "port": "<mcp_server_port>",
  "database_user": "<database_user>",
  "database_password": "<database_password>",
  "log_level": "INFO",
  "ssl_certfile": "/app/server.crt",
  "ssl_keyfile": "/app/server.key",
  "oauth": {
	"FASTMCP_SERVER_AUTH_CONFIG_URL": "<oidc_discovery_url>",
	"FASTMCP_SERVER_AUTH_CLIENT_ID": "<client_id>",
	"FASTMCP_SERVER_AUTH_CLIENT_SECRET": "<client_secret>",
	"FASTMCP_SERVER_AUTH_BASE_URL": "<server_base_url>",
	"FASTMCP_SERVER_AUTH_AUDIENCE": "<audience>",
	"user_impersonation": true
  }
}
```

### Configuration reference

**Required fields**

| Field | Type | Description |
|-------|------|-------------|
| `driver` | `string` | ODBC driver name used to connect to Analytics Engine |
| `server` | `string` | Host or connection target for the Analytics Engine database |
| `database` | `string` | Name of the database. |
| `max_connections` | `integer` | Maximum concurrent database connections in the pool|
| `host` | `string` | Host address that the MCP Server listens to in the container |
| `port` | `string` | Port that the MCP Server listens to in the container |
| `database_user` | `string` | Database username|
| `database_password` | `string` | Database password |

**Optional fields**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_rows` | `integer` | `1000` | Maximum number of rows returned per query response. Default is `1000`.|
--8<-- "conf/common-optional-fields.md"
--8<-- "conf/tls-fields.md"
--8<-- "conf/write-fields.md"


## Start the server

With `conf.json` ready, start the container and mount the configuration file as a
read-only volume:

```bash
docker run -d \
    -v $(pwd)/conf.json:/app/conf.json:ro \
    -p 8000:8000 \
    --name=actian-mcp \
    actian/analytics-engine-mcp-server:1.0.0
```

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
  Learn more about the Analytics Engine tools used by the MCP Server.

- :material-folder-open: **[Resources](resources/index.md)**  
  Explore the resource types available through the server.

- :material-message-text: **[Prompts](prompts/index.md)**  
  Use the built-in prompt templates for common workflows.

- :material-puzzle: **[Extensions](../extensions/index.md)**  
  Add your own tools to the server with a Python extension.

</div>
