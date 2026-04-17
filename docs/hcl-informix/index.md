---
title: HCL Informix®
description: Use the Actian MCP Server to connect MCP clients to HCL Informix® Database.
---

# HCL Informix®

Connect your MCP-compatible client to **HCL Informix® Database** using the Actian MCP Server. Once configured, clients can explore schema metadata and execute read-only SQL queries through a standard interface.


## Overview

The HCL Informix® MCP Server acts as a bridge between any MCP client and your HCL Informix® database. It automatically handles connection pooling, response formatting, and schema discovery, so you can focus on your queries.

### Capabilities

| Action | Description |
|--------|-------------|
| **Run SQL queries** | Execute read-only SQL against your database. |
| **List tables and views** | Discover available objects in the schema. |
| **Inspect table structure** | Retrieve column definitions, types, and key information. |
| **Read schema metadata** | Explore database-level metadata. |
| **List functions and procedures** | View available user-defined routines. |


## Prerequisites

- Docker or Podman installed and running.
- Access credentials for your HCL Informix® database.
- (Optional) TLS certificate and key files for secure deployments.
- (Optional) An OIDC provider if using OAuth authentication.


## Configuration

The server is distributed as a Docker container. You supply a single JSON configuration file that is mounted into the container at `/app/conf.json`.

### Create the Configuration File

Create a file named `conf.json` in your working directory:

```json
{
  "servername": "<server_name>",
  "service": "<service_port>",
  "dsn": "<dsn_name>",
  "server": "<database_host>",
  "database": "<database_name>",
  "database_user": "<database_user>",
  "database_password": "<database_password>",
  "max_connections": "<max_concurrent_connections>",
  "max_rows": "<max_rows_per_query_response>",
  "host": "<mcp_server_host>",
  "port": "<mcp_server_port>",
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
| `servername` | `string` | HCL Informix® database server name. |
| `service` | `integer` | HCL Informix® server port number. |
| `dsn` | `string` | Data source name. |
| `server` | `string` | Host address for the HCL Informix® database. |
| `database` | `string` | Name of the database to connect to. |
| `max_connections` | `integer` | Maximum concurrent database connections in the pool. |
| `host` | `string` | Host address that the MCP Server listens on inside the container. |
| `port` | `string` | Port that the MCP Server listens on inside the container. |
| `database_user` | `string` | Database username (can also be provided on the command line). |
| `database_password` | `string` | Database password (can also be provided on the command line). |

**Optional fields**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_rows` | `integer` | `1000` | Maximum number of rows returned per query response. |
| `ssl_certfile` | `string` | — | Path to the TLS certificate file. Always `/app/server.crt` inside the container. |
| `ssl_keyfile` | `string` | — | Path to the TLS private key file. Always `/app/server.key` inside the container. |
| `oauth` | `object` | — | OAuth configuration block for protected deployments. See [OAuth configuration](../authentication/index.md#the-oauth-configuration-block). |

---

## Start the Server

In the conf.json set host address to 0.0.0.0. With your `conf.json` file ready, start the container and mount the configuration file as `/app/conf.json`:

```bash
docker load -i ifx_mcp_image.tar

docker run -p 8000:8000 -d --name ifx-mcp \
  -v $(pwd)/conf_temp.json:/app/conf.json:ro,Z \
  actian/informix-mcp-server-linux:1.0.0
```

!!! note The container always reads its configuration from /app/conf.json. Do not change the mount target path.

Once the container is running, connect your MCP client to the exposed server endpoint using the host and port from your configuration like "https://<host machine ip address>:8000/mcp"

---

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](tools/index.md)**  
  Explore the available MCP tools for HCL Informix® database operations.

- :material-folder-open: **[Resources](resources/index.md)**  
  Learn about schema metadata resources.

- :material-chat-processing: **[Prompts](prompts/index.md)**  
  Discover pre-built prompt templates for common workflows.

</div>