---
title: Actian Ingres
description: Use the Actian MCP Server to connect MCP clients to Actian Ingres.
---

# Actian Ingres

Connect your MCP-compatible client to **Actian Ingres** using the Actian MCP Server. Once configured, clients can explore schema metadata and execute read-only SQL queries through a standard interface.


## Overview

The Ingres MCP Server acts as a bridge between any MCP client and your Actian Ingres database. It automatically handles connection pooling, response formatting, and schema discovery, so you can focus on your queries.

### Capabilities

| Action | Description |
|--------|-------------|
| **Run SQL queries** | Execute read-only SQL against your database. |
| **List tables and views** | Discover available objects in the schema. |
| **Inspect table structure** | Retrieve column definitions, types, and comments. |
| **Read schema metadata** | Explore database-level metadata with constraint information. |
| **List functions and procedures** | View available user-defined routines. |


## Prerequisites

- Docker installed and running.
- Access credentials for your Actian Ingres database.
- (Optional) TLS certificate and key files for secure deployments.
- (Optional) An OIDC provider if using OAuth authentication.


## Configuration

The server is distributed as a Docker container. You supply a single JSON configuration file that is mounted into the container at `/app/conf.json`.

### Create the Configuration File

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
    "user_impersonation": true
  }
}
```

### Configuration Reference

**Required Fields**

| Field | Type | Description |
|-------|------|-------------|
| `driver` | `string` | ODBC driver name used to connect to Ingres. |
| `server` | `string` | Host or connection target for the Ingres database. |
| `database` | `string` | Name of the database to connect to. |
| `max_connections` | `integer` | Maximum concurrent database connections in the pool. |
| `host` | `string` | Host address that the MCP Server listens on inside the container. |
| `port` | `string` | Port that the MCP Server listens on inside the container. |
| `database_user` | `string` | Database username. |
| `database_password` | `string` | Database password. |

**Optional Fields**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_rows` | `integer` | `1000` | Maximum number of rows returned per query response. |
| `ssl_certfile` | `string` | — | Path to the TLS certificate file. |
| `ssl_keyfile` | `string` | — | Path to the TLS private key file. |
| `oauth` | `object` | — | OAuth configuration block for protected deployments. See [OAuth configuration](../authentication/index.md#the-oauth-configuration-block). |

---

## Start the Server

With your `conf.json` file ready, start the container and mount the configuration file:

```bash
docker run -d \
  -v $(pwd)/conf.json:/app/conf.json:ro \
  actian/ingres-mcp-server:1.0.0
```

Once the container is running, connect your MCP client to the exposed server endpoint using the host and port from your configuration.

---

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](tools/index.md)**  
  Explore the available MCP tools for Ingres database operations.

- :material-folder-open: **[Resources](resources/index.md)**  
  Learn about schema metadata resources.

- :material-chat-processing: **[Prompts](prompts/index.md)**  
  Discover pre-built prompt templates for common workflows.

</div>
