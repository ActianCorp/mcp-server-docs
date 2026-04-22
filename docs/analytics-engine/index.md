---
title: Actian Analytics Engine
description: Connect MCP clients to Actian Analytics Engine for schema exploration and read-only SQL queries.
---

# Actian MCP Server for Analytics Engine

Connect the MCP-compatible client to the Actian Analytics Engine using the Actian MCP Server. This setup allows you to explore schema metadata and execute read-only SQL queries through a standard interface. The MCP Server for Analytics Engine bridges the gap between the MCP client and the Actian database. The server manages connection pooling, response formatting, and schema discovery automatically, allowing you to focus on the data.


### Capabilities

The Actian Analytics Engine MCP Server supports the following operations:

| Action | Description |
|--------|-------------|
| **Execute SQL queries** | Execute read-only SQL against the database |
| **List tables and views** | Discover available objects in the schema |
| **Inspect table structure** | Retrieve column definitions and types |
| **Read schema metadata** | Explore database-level metadata |
| **List functions and procedures** | View available user-defined functions and procedures |


## Prerequisites

Before starting the server, ensure the following requirements are met:

- **Container Engine:** Docker installed and running on the host machine.
- **Database credentials:** Valid access for the Analytics Engine database.
- **Security files (optional):** TLS certificate and key files for secure deployments.
- **OIDC provider (optional):** Required if you are using OAuth authentication.


## Configuration

The server runs as a Docker container. To configure the server, mount the (`conf.json`) file to the container at `/app/conf.json`.

### Create the Configuration File

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

### Configuration Reference

**Required Fields**

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
| `log_level` | `string` | `INFO` | Server log verbosity. Valid values are `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `ssl_certfile` | `string` | — | Path to the TLS certificate file. Add `/app/server.crt` in the container. |
| `ssl_keyfile` | `string` | — | Path to the TLS private key file. Add `/app/server.key` in the container. |
| `oauth` | `object` | — | OAuth configuration block for protected deployments. For more information, see [OAuth configuration](../authentication/index.md#the-oauth-configuration-block).|


## Start the Server

Once you have created the `conf.json` file, start the container and mount the configuration file:

```bash
docker run -d \
  -v $(pwd)/conf.json:/app/conf.json:ro \
  actian/analytics-engine-mcp-server:1.0.0
```

!!! important
	The container reads its configuration from `/app/conf.json`. Do not change the mount target path.

After the container starts, connect the MCP client to the server endpoint using the host and port specified in `conf.json`.


## Usage

Once connected, the MCP client automatically discovers the server capabilities. You can perform the following tasks:

- **Inspect before querying**: List tables and review structure before writing SQL.
- **Run a query**: Execute a read-only SQL statement and receive formatted results.
- **Explore functions**: Look up available user-defined functions and stored procedures.
- **Summarize results**: Ask the client to interpret or summarize query output.


## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](tools/index.md)**  
  Learn more about the Analytics Engine tools used by the MCP Server.

- :material-folder-open: **[Resources](resources/index.md)**  
  Explore the resource types available through the server.

- :material-message-text: **[Prompts](prompts/index.md)**  
  Use the built-in prompt templates for common workflows.

</div>
