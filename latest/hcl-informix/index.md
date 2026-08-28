---
title: HCL Informix®
description: Use the Actian MCP Server to connect MCP clients to HCL Informix® Database.
---

# Actian MCP Server for HCL Informix®

Connect the MCP-compatible client to an HCL Informix® database using the Actian MCP Server. Once configured, you can use the server to explore schema metadata and execute SQL queries through a standardized interface. The MCP Server for HCL Informix® enables communication between any MCP client and the HCL Informix® database. The server automatically manages connection pooling, response formatting, and schema discovery, allowing you to focus on business data analysis.


## Capabilities

The Actian MCP Server for HCL Informix® supports the following operations:

| Action | Description |
|--------|-------------|
| **Run SQL queries** | Run read-only SQL directly against the database.|
| **List tables and views** | Discover available objects within the schema. |
| **Inspect table structure** | Retrieve column definitions, data types, and key information. |
| **Read schema metadata** | Explore comprehensive database-level metadata. |
| **List functions and procedures** | View available user-defined routines. |
| **Execute write queries** | Run `INSERT`, `UPDATE`, and `DELETE` statements. Off by default. Requires `query_mode` set to `read-write`. |

!!! note "Write support is opt-in"
    The server permits only read queries unless you set `query_mode` to `read-write`. Each write then requires the `mcp:write` scope and human approval. For more information, see [Write support](write-support.md).

---

## Prerequisites

Before starting the server, ensure the following requirements are met:

* **Container Engine:** Docker installed and running on the host machine.
* **Database credentials:** Access details for the HCL Informix database.
* **Secure deployment files (Optional):** TLS certificate and key files.
* **Authentication (Optional):** An OIDC provider, required for OAuth authentication.

!!! note "Database Compatibility"
    The Actian MCP server for HCL Informix requires version 15.0.1 and above. Earlier Informix versions are not supported.

---

## Configuration

The server runs as a Docker container. To configure the server, mount the (`conf.json`) file to the container at `/app/conf.json`.

### Create Configuration File

Create a file named `conf.json` in the working directory and add the database-specific configuration details:

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
  "query_mode": "read-only",
  "write_confirmation": true,
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
| `max_connections` | integer | Maximum concurrent database connections in the pool|
| `host` | `string` | Host address that the MCP Server listens on inside the container|
| `port` | integer | Port that the MCP Server listens on inside the container |
| `database_user` | `string` | Database username. |
| `database_password` | `string` | Database password. |

**Optional Fields**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_rows` | integer | 1000 | Maximum number of rows returned per query response. |
| `log_level` | `string` | `INFO` | Server log verbosity. Valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `ssl_certfile` | `string` | — | Path to the TLS certificate file. Add `/app/server.crt` inside the container. |
| `ssl_keyfile` | `string` | — | Path to the TLS private key file. Add `/app/server.key` inside the container. |
| `oauth` | `object` | — | OAuth configuration block for protected deployments, see [OAuth configuration](authentication/index.md#configuring-oauth-block) for more information. |
| `query_mode` | `string` | `read-only` | Controls whether data-modifying SQL is permitted. Valid values are `read-only` and `read-write`. See [Write support](write-support.md) |
| `write_confirmation` | `boolean` | `true` | Whether a write requires human approval before it runs. Set to `false` only for clients that cannot display the approval prompt. See [Write support](write-support.md#skipping-the-approval-prompt). Applies only when `query_mode` is `read-write`. |
| `extensions` | `array` | — | Extension modules to load, each object with a required `module` and an optional `config`. For more information, see [Extensions](extensions/index.md) |

---

## Start the Server

With the `conf.json` file ready, run the following Docker command to start the container. This command mounts the configuration file as a read-only volume.

    ```bash
    docker run  -d \
      -v $(pwd)/conf_temp.json:/app/conf.json:ro,Z \
      -p 8000:8000 \
      --name=ifx-mcp \
      actian/informix-mcp-server:1.1.0
    ```

!!! note 
    The container must read its configuration from `/app/conf.json`. Do not change the mount target path.

Once the container is running, connect the MCP client to the exposed server endpoint using the host and port from the configuration `"https://<host machine ip address>:8000/mcp"`

---

## Next Steps

<div class="grid cards" markdown>

- :material-pencil: **[Write Support](write-support.md)**  
  Enable data-modifying SQL, and what gates each write.

- :material-lock: **[Authentication](authentication/index.md)**  
  Secure the server with OAuth 2.0 and an external identity provider.

- :material-tools: **[Tools](tools/index.md)**  
  Explore the available MCP tools for HCL Informix® database operations.

- :material-folder-open: **[Resources](resources/index.md)**  
  Learn more about schema metadata resources.

- :material-chat-processing: **[Prompts](prompts/index.md)**  
  Use pre-built prompt templates for common workflows.

- :material-puzzle: **[Extensions](extensions/index.md)**  
  Add your own tools to the server with a Python extension.

</div>
