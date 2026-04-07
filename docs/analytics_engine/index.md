---
title: Actian Analytics Engine
description: Connect MCP clients to Actian Analytics Engine for schema exploration and read-only SQL queries.
---

# Actian Analytics Engine

Connect your MCP-compatible client to **Actian Analytics Engine** using the Actian MCP Server. Once configured, clients can explore schema metadata and execute read-only SQL queries through a standard interface.


## Overview

The Analytics Engine MCP Server acts as a bridge between any MCP client and your Actian database. It handles connection pooling, response formatting, and schema discovery automatically — so you can focus on your queries.

### Capabilities

| Action | Description |
|--------|-------------|
| **Run SQL queries** | Execute read-only SQL against your database |
| **List tables and views** | Discover available objects in the schema |
| **Inspect table structure** | Retrieve column definitions and types |
| **Read schema metadata** | Explore database-level metadata |
| **List functions and procedures** | View available user-defined routines |


## Prerequisites

- Docker installed and running
- Access credentials for your Analytics Engine database
- (Optional) TLS certificate and key files for secure deployments
- (Optional) An OIDC provider if using OAuth authentication


## Configuration

The server is distributed as a Docker container. You supply a single JSON configuration file that is mounted into the container at `/app/conf.json`.

### Create the configuration file

Create a file named `conf.json` in your working directory:

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
  "ssl_certfile": "<path_to_ssl_certificate_file>",
  "ssl_keyfile": "<path_to_ssl_private_key_file>",
  "oauth": {
	"FASTMCP_SERVER_AUTH_CONFIG_URL": "<oidc_discovery_url>",
	"FASTMCP_SERVER_AUTH_CLIENT_ID": "<client_id>",
	"FASTMCP_SERVER_AUTH_CLIENT_SECRET": "<client_secret>",
	"FASTMCP_SERVER_AUTH_BASE_URL": "<server_base_url>",
	"FASTMCP_SERVER_AUTH_AUDIENCE": "<audience>",
	"FASTMCP_SERVER_AUTH_SCOPE": "<scopes>",
	"user_impersonation": true
  }
}
```

### Configuration reference

**Required fields**

| Field | Type | Description |
|-------|------|-------------|
| `driver` | `string` | ODBC driver name used to connect to Analytics Engine. |
| `server` | `string` | Host or connection target for the Analytics Engine database. |
| `database` | `string` | Name of the database to connect to. |
| `max_connections` | `integer` | Maximum concurrent database connections in the pool. |
| `host` | `string` | Host address that the MCP Server listens on inside the container. |
| `port` | `string` | Port that the MCP Server listens on inside the container. |
| `database_user` | `string` | Database username. |
| `database_password` | `string` | Database password. |

**Optional fields**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_rows` | `integer` | `1000` | Maximum number of rows returned per query response. |
| `ssl_certfile` | `string` | — | Path to the TLS certificate file. |
| `ssl_keyfile` | `string` | — | Path to the TLS private key file. |
| `oauth` | `object` | — | OAuth configuration block for protected deployments. See [OAuth configuration](../authentication/index.md#the-oauth-configuration-block). |

---

## Start the server

With your `conf.json` ready, start the container and mount the configuration file:

```bash
docker run -d \
  -v $(pwd)/conf.json:/app/conf.json:ro \
  actian/analytics-engine-mcp-server:1.0.0
```

!!! note
	The container always reads its configuration from `/app/conf.json`. Do not change the mount target path.

Once the container is running, connect your MCP client to the server endpoint using the host and port you specified in `conf.json`.


## Usage

After connecting, your MCP client automatically discovers the server's capabilities. Common tasks include:

- **Inspect before querying** — List tables and review structure before writing SQL.
- **Run a query** — Execute a read-only SQL statement and receive formatted results.
- **Explore functions** — Look up available user-defined functions and stored procedures.
- **Summarize results** — Ask the client to interpret or summarize query output.


## Next steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](tools/index.md)**  
  Learn about the Analytics Engine tools exposed by the MCP Server.

- :material-folder-open: **[Resources](resources/index.md)**  
  Explore the resource types available through the server.

- :material-message-text: **[Prompts](prompts/index.md)**  
  Review the built-in prompt templates for common workflows.

</div>
