---
title: Actian Analytics Engine
description: Connect MCP clients to Actian Analytics Engine for schema exploration and SQL queries, with optional write support.
---

# Actian MCP Server for Analytics Engine

Connect the MCP-compatible client to the Actian Analytics Engine using the Actian MCP Server. With this setup, the client can explore schema metadata and run SQL queries through a standard interface. Queries are read-only unless you enable write mode. The MCP Server for Analytics Engine bridges the gap between the MCP client and the Actian database. The server manages connection pooling, response formatting, and schema discovery automatically.

Analytics Engine runs in two deployments, and the MCP Server supports both:

- **Self-hosted.** You run Analytics Engine on your own infrastructure, on premises or in your own cloud account, and you deploy the MCP Server alongside it.
- **SaaS.** Analytics Engine powers the warehouse on the Actian Analytics AI Platform, and the MCP Server is configured for you.

The tools, resources, and prompts are the same in both deployments. Only the setup and the connection details differ.


## Deployment Options

### Self-Hosted

You run the MCP Server in a container alongside your own Analytics Engine instance. You supply the database connection details in `conf.json`, secure the endpoint, and manage the server lifecycle. The rest of this page describes that setup.

### SaaS

The MCP Server is deployed and configured with the warehouse. There is nothing to install and no configuration file to write. The client connects to a URL specific to that warehouse and signs in with OAuth, and your existing database privileges apply to every query.

For instructions, see [SaaS deployment](managed-warehouse.md).


## Capabilities

The Actian Analytics Engine MCP Server supports the following operations:

| Action | Description |
|--------|-------------|
| **Execute SQL queries** | Execute read-only SQL against the database |
| **List tables and views** | Discover available objects in the schema |
| **Inspect table structure** | Retrieve column definitions and types |
| **Read schema metadata** | Explore database-level metadata |
| **List functions and procedures** | View available user-defined functions and procedures |
| **Execute write queries** | Run `INSERT`, `UPDATE`, `DELETE`, and `MERGE` statements. Off by default. Requires `query_mode` set to `read-write` |

!!! note "Write support is opt-in"
    The server permits only read queries unless you set `query_mode` to `read-write`. Each write then requires the `mcp:write` scope and human approval. For more information, see [Write support](write-support.md).


## Prerequisites

The following sections apply to a self-hosted deployment. Before starting the server, ensure the following requirements are met:

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
  "driver": "{Ingres}",
  "server": "@<db-host>,tcp_ip,<installation_id>",
  "database": "<database_name>",
  "max_connections": 10,
  "max_rows": 1000,
  "host": "<mcp_server_host>",
  "port": 8000,
  "query_mode": "read-only",
  "write_confirmation": true,
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
| `port` | `integer` | Port that the MCP Server listens to in the container |
| `database_user` | `string` | Database username|
| `database_password` | `string` | Database password |

**Optional fields**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_rows` | `integer` | `1000` | Maximum number of rows returned in a single query response. A statement that matches more rows is truncated to this limit, and the response includes the `truncated` and `warning` fields. Default is `1000`. |
| `log_level` | `string` | `INFO` | Server log verbosity. Valid values are `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `ssl_certfile` | `string` | None | Path to the TLS certificate file. Add `/app/server.crt` in the container. |
| `ssl_keyfile` | `string` | None | Path to the TLS private key file. Add `/app/server.key` in the container. |
| `oauth` | `object` | None | OAuth configuration block for protected deployments. For more information, see [OAuth configuration](authentication/index.md#configuring-oauth-block).|
| `query_mode` | `string` | `read-only` | Controls whether data-modifying SQL is permitted. Valid values are `read-only` and `read-write`. See [Write support](write-support.md).|
| `write_confirmation` | `boolean` | `true` | Whether a write requires human approval before it runs. Set to `false` only for clients that cannot display the approval prompt. See [Write support](write-support.md#skipping-the-approval-prompt). Applies only when `query_mode` is `read-write`. |
| `extensions` | `array` | None | Extension modules to load, each an object with a required `module` and an optional `config`. For more information, see [Extensions](extensions/index.md).|


## Start the Server

Once you have created the `conf.json` file, start the container and mount the configuration file:

```bash
docker run -d \
    -v $(pwd)/conf.json:/app/conf.json:ro \
    -p 8000:8000 \
    --name=actian-mcp \
    actian/analytics-engine-mcp-server:1.1.0
```


!!! important
	The container reads its configuration from `/app/conf.json`. Do not change the mount target path.

After the container starts, connect the MCP client to the server endpoint using the host and port specified in `conf.json`.


## Usage

Once connected, the MCP client automatically discovers the server capabilities. You can perform the following tasks:

- **Inspect before querying**: List tables and review structure before writing SQL.
- **Run a query**: Execute a SQL statement and receive formatted results.
- **Explore functions**: Look up available user-defined functions and stored procedures.


## Next Steps

<div class="grid cards" markdown>

- :material-pencil: **[Write Support](write-support.md)**  
  Enable data-modifying SQL, and what gates each write.

- :material-lock: **[Authentication](authentication/index.md)**  
  Secure the server with OAuth 2.0 and an external identity provider.

- :material-tools: **[Tools](tools/index.md)**  
  Learn more about the Analytics Engine tools used by the MCP Server.

- :material-folder-open: **[Resources](resources/index.md)**  
  Explore the resource types available through the server.

- :material-message-text: **[Prompts](prompts/index.md)**  
  Use the built-in prompt templates for common workflows.

- :material-puzzle: **[Extensions](extensions/index.md)**  
  Add custom tools to the server with a Python extension.

</div>