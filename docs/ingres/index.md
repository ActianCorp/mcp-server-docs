---
title: Actian Ingres
description: Use the Actian MCP Server to connect MCP clients to Actian Ingres.
---

# Actian Ingres MCP Server

Connect the MCP-compatible client to Actian Ingres using the Actian MCP Server. This bridge allows the clients to explore schema metadata and execute read-only SQL queries through a standard interface. The server manages connection pooling, response formatting, and schema discovery automatically, allowing you to focus on data analysis.

## Capabilities

The Actian Ingres MCP Server supports the following operations:

| Action | Description |
| :--- | :--- |
| **Run SQL queries** | Execute read-only SQL against the database. |
| **List tables and views** | Discover available objects in the schema. |
| **Inspect table structure** | Retrieve column definitions, types, and comments. |
| **Read schema metadata** | Explore database-level metadata and constraints. |
| **List functions** | View available user-defined routines and procedures. |

---

## Prerequisites
Before starting the server, ensure to meet the following requirements:

* **Docker:** Installed and running on the host machine.
* **Database Access:** Valid credentials for the Actian Ingres instance.
* **Security (Optional):** TLS certificate and key files for secure deployments.
* **Authentication (Optional):** An OIDC provider, if you require OAuth.

---


## Configuration

The server runs as a Docker container. You must provide a `conf.json` configuration file and mount it to the `/app/conf.json` path in the container.

### Create Configuration File
Create a file named `conf.json` in the working directory and define the environment variables:

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
| `driver` | `string` | The ODBC driver name for the Ingres connection. |
| `server` | `string` | The host or connection target for the Ingres database. |
| `database` | `string` |The name of the target database. |
| `max_connections` | `integer` | Maximum concurrent database connections in the pool. |
| `host` | `string` | The host address the server listens to in the container. |
| `port` | `string` | The port the server listens to in the container (typically `8000`). |
| `database_user` | `string` | The username for database authentication. |
| `database_password` | `string` | The password for database authentication. |

**Optional Fields**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_rows` | `integer` | `1000` | The maximum number of rows returned in a single query response.  |
| `log_level` | `string` | `INFO` | Server log verbosity. Valid values are `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `ssl_certfile` | `string` | — | Path to the TLS certificate file. Set `/app/server.crt` in the container. |
| `ssl_keyfile` | `string` | — | Path to the TLS private key file. Set `/app/server.key` in the container. |
| `oauth` | `object` | — | OAuth configuration block for protected deployments. For more information, see [OAuth configuration](../authentication/index.md#the-oauth-configuration-block). |

---

## Start the Server

With the `conf.json` file ready, run the following Docker command to start the container. This command mounts the configuration file as a read-only volume.

```bash
docker run -d \
  -v $(pwd)/conf.json:/app/conf.json:ro \
  actian/ingres-mcp-server:1.0.0
```

Once the container is running, you can connect the MCP client to the server using the host and port specified in the configuration.

---

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](tools/index.md)**  
  Explore the available MCP tools for Ingres database operations.

- :material-folder-open: **[Resources](resources/index.md)**  
  Learn about schema metadata resources.

- :material-chat-processing: **[Prompts](prompts/index.md)**  
  Access pre-built templates for common database workflows.

</div>
