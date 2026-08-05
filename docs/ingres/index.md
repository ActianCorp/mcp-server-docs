---
title: Actian Ingres
description: Use the Actian MCP Server to connect MCP clients to Actian Ingres.
---

# Actian MCP Server for Ingres

Connect the MCP-compatible client to Actian Ingres using the Actian MCP Server. This bridge allows the clients to explore schema metadata and run SQL queries through a standard interface. Queries are read-only unless you enable write mode. The server manages connection pooling, response formatting, and schema discovery automatically, allowing you to focus on data analysis.

## Capabilities

The Actian MCP Server for Ingres supports the following operations:

| Action | Description |
| :--- | :--- |
| **Execute SQL queries** | Execute read-only SQL against the database |
| **List tables and views** | Discover available objects in the schema |
| **Describe table structure** | Retrieve column definitions, types, and comments|
| **Read schema metadata** | Explore database-level metadata and constraints |
| **List functions** | View available user-defined functions and procedures|
| **Execute write queries** | Run `INSERT`, `UPDATE`, and `DELETE` statements. Off by default. Requires `query_mode` set to `read-write` |

!!! note "Write support is opt-in"
    The server permits only read queries unless you set `query_mode` to `read-write`. Each write then requires the `mcp:write` scope and human approval. For more information, see [Write support](../intro/write-support.md).

---

## Prerequisites
Before starting the server, ensure the following requirements are met:

* **Container Engine:** Docker installed and running on the host machine.
* **Database Access:** Valid credentials for the Actian Ingres instance
* **Security (Optional):** TLS certificate and key files for secure deployments
* **Authentication (Optional):** An OIDC provider, if you require OAuth

---


## Configuration

The server runs as a Docker container. To configure the server, mount the (`conf.json`) file to the container at `/app/conf.json`.

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
| `driver` | `string` | The ODBC driver name for the Ingres connection |
| `server` | `string` | The host or connection target for the Ingres database |
| `database` | `string` |The name of the target database |
| `max_connections` | `integer` | Maximum concurrent database connections in the pool |
| `host` | `string` | The host address the server listens to in the container. |
| `port` | `string` | The port the server listens to in the container (typically `8000`)|
| `database_user` | `string` | The username for database authentication|
| `database_password` | `string` | The password for database authentication |

**Optional Fields**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_rows` | `integer` | `1000` | The maximum number of rows returned in a single query response. Maximum value: `1000` |
--8<-- "conf/common-optional-fields.md"
--8<-- "conf/tls-fields.md"
--8<-- "conf/write-fields.md"

---

## Start the server

With `conf.json` ready, start the container and mount the configuration file as a
read-only volume:

```bash
docker run -d \
    -v $(pwd)/conf.json:/app/conf.json:ro \
    -p 8000:8000 \
    --name=actian-mcp \
    actian/ingres-mcp-server:1.0.0
```

--8<-- "docker/mount-path-note.md"
--8<-- "conf/protection-note.md"

## Verify the connection

--8<-- "verify-connection.md"

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](tools/index.md)**  
  Explore the available MCP tools for Ingres database operations

- :material-folder-open: **[Resources](resources/index.md)**  
  Learn about schema metadata resources

- :material-chat-processing: **[Prompts](prompts/index.md)**  
  Access pre-built templates for common database workflows

- :material-puzzle: **[Extensions](../extensions/index.md)**  
  Add your own tools to the server with a Python extension.

</div>
