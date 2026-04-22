---
title: HCL Informix®
description: Use the Actian MCP Server to connect MCP clients to HCL Informix® Database.
---

# HCL Informix® MCP Server

Connect the MCP-compatible client to an HCL Informix® database using the Actian MCP Server. Once configured, you can use the server to explore schema metadata and execute read-only SQL queries through a standardized interface. The HCL Informix® MCP Server enables communication between any MCP client and the HCL Informix® database. The server automatically manages connection pooling, response formatting, and schema discovery, allowing you to focus on writing queries.


### Capabilities

The HCL Informix® MCP Server supports the following operations:

| Action | Description |
|--------|-------------|
| **Run SQL queries** | Run read-only SQL directly against the database.|
| **List tables and views** | Discover available objects within the schema. |
| **Inspect table structure** | Retrieve column definitions, data types, and key information. |
| **Read schema metadata** | Explore comprehensive database-level metadata. |
| **List functions and procedures** | View available user-defined routines. |


## Prerequisites

Before starting the server, ensure the following requirements are met:

- **Container Engine:** Docker or Podman installed and running on the host machine.
- **Database credentials:** Access details for the HCL Informix database.
- **Secure deployment files (Optional):** TLS certificate and key files.
- **OIDC provider (Optional):** Required if you are using OAuth authentication.


## Configuration

The server runs as a Docker container. To configure the server, mount the (`conf.json`) file to the container at `/app/conf.json`.

### Create Configuration File

Create a file named `conf.json` in the working directory and include the specific database details:

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
| `servername` | `string` | HCL Informix® database server name |
| `service` | `integer` | HCL Informix® server port number |
| `dsn` | `string` | Data source name |
| `server` | `string` | Host address for the HCL Informix® database |
| `database` | `string` | Name of the database to connect to target database |
| `max_connections` | `integer` | Maximum concurrent database connections in the pool|
| `host` | `string` | Host address that the MCP Server listens on inside the container|
| `port` | `string` | Port that the MCP Server listens on inside the container |
| `database_user` | `string` | Database username. You can also provide in the command line |
| `database_password` | `string` | Database password. You can also provide in the command line |

**Optional fields**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_rows` | `integer` | `1000` | Maximum number of rows returned per query response. |
| `log_level` | `string` | `INFO` | Server log verbosity. Valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `ssl_certfile` | `string` | — | Path to the TLS certificate file. Add `/app/server.crt` inside the container. |
| `ssl_keyfile` | `string` | — | Path to the TLS private key file. Add `/app/server.key` inside the container. |
| `oauth` | `object` | — | OAuth configuration block for protected deployments, see [OAuth configuration](../authentication/index.md#the-oauth-configuration-block) for more information. |

---

## Start the Server

In the `conf.json` set host address to `0.0.0.0`. Once the `conf.json` file is ready, start the container and mount the configuration file as `/app/conf.json`:


1. Load the image:

    ```bash
    docker load -i ifx_mcp_image.tar
    ```

2. Run the container:

    ```bash
    docker run -p 8000:8000 -d --name ifx-mcp \
      -v $(pwd)/conf_temp.json:/app/conf.json:ro,Z \
      actian/informix-mcp-server-linux:1.0.0
    ```

!!! note 
    The container must read its configuration from `/app/conf.json`. Do not change the mount target path.

Once the container is running, connect the MCP client to the exposed server endpoint using the host and port from the configuration `"https://<host machine ip address>:8000/mcp"`

---

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](tools/index.md)**  
  Explore the available MCP tools for HCL Informix® database operations.

- :material-folder-open: **[Resources](resources/index.md)**  
  Learn more about schema metadata resources.

- :material-chat-processing: **[Prompts](prompts/index.md)**  
  Use pre-built prompt templates for common workflows.

</div>