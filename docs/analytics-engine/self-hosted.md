---
title: Self-Hosted
description: Deploy and configure the Actian MCP Server against an Analytics Engine instance that you run.
---

# Actian MCP Server for Analytics Engine (Self-Hosted)

This page describes how to run the MCP Server against an Analytics Engine instance that you host yourself, on premises or in your own cloud account. You deploy the server in a container, supply the database connection details, and manage the server lifecycle.

If Analytics Engine powers a warehouse on the Actian Analytics AI Platform, the MCP Server is configured for you. See [SaaS](saas.md).


## Prerequisites

Before starting the server, ensure the following requirements are met:

- **Container Engine:** Docker installed and running on the host machine.
- **Database credentials:** Valid access for the Analytics Engine database.
- **Security files (optional):** TLS certificate and key files for secure deployments.
- **OIDC provider (optional):** Required if you are using OAuth authentication.


## Configuration

The server runs as a Docker container. To configure the server, mount the `conf.json` file to the container at `/app/conf.json`.

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
| `max_rows` | `integer` | `1000` | Maximum number of rows returned in a single query response. A statement that matches more rows is truncated to this limit, and the response includes the `truncated` and `warning` fields. |
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

After the container starts, connect the MCP client to the server endpoint using the host and port specified in `conf.json`. For client configuration examples, see [Connecting MCP Clients](../mcp-clients/index.md).


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

- :material-puzzle: **[Extensions](extensions/index.md)**  
  Add custom tools to the server with a Python extension.

</div>