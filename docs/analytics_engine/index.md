---
title: Actian Analytics Engine
description: Use the Actian MCP Server to connect MCP clients to Actian Analytics Engine.
---

# Actian Analytics Engine

This page explains how to use the **Actian MCP Server** with **Actian Analytics Engine**.

When configured for Analytics Engine, the server gives an MCP-compatible client a simple way to explore schema information and run read-only database queries through a standard interface.

---

## What You Can Do

With the Analytics Engine server, AI clients can:

- Run **read-only SQL queries**
- List available tables and views
- Inspect the structure of a specific table
- Read database schema metadata
- List user-defined functions and procedures

---

## Configuration

When the server is provided as a Docker container, the main user-provided input is a JSON configuration file that is mounted into the container.

The Analytics Engine container starts the MCP Server in **HTTP transport** mode by default, so the configuration should include the network settings the container will use.

Create a file such as `conf.json` with the following structure:

```json
{
	"driver": "<odbc_driver>",
	"server": "<database_host>",
	"database": "<database_name>",
	"max_connections": "<max_concurrent_connections_to_database>",
	"max_rows": "<max_number_of_rows_to_retrieve_from_database>",
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

Use these fields as follows:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `driver` | `str` | Yes | ODBC driver name used to connect to Actian Analytics Engine |
| `server` | `str` | Yes | Host or connection target for the Analytics Engine database |
| `database` | `str` | Yes | Name of the database the MCP Server connects to |
| `max_connections` | `int` | Yes | Maximum number of concurrent database connections the server keeps in its pool |
| `max_rows` | `int` | No | Maximum number of rows returned for a single query response; defaults to `1000` |
| `host` | `str` | Yes | Host address the MCP Server listens on inside the container |
| `port` | `str` | Yes | Port the MCP Server listens on inside the container |
| `database_user` | `str` | Yes | Database user name used to authenticate to Analytics Engine |
| `database_password` | `str` | Yes | Database password used to authenticate to Analytics Engine |
| `ssl_certfile` | `str` | No | Path to the TLS certificate file inside the deployment |
| `ssl_keyfile` | `str` | No | Path to the TLS private key file inside the deployment |
| `oauth` | `object` | No | OAuth configuration block for protected MCP server deployments |
| `oauth.FASTMCP_SERVER_AUTH_CONFIG_URL` | `str` | No | OIDC discovery URL used by the MCP Server |
| `oauth.FASTMCP_SERVER_AUTH_CLIENT_ID` | `str` | No | OAuth client ID for the MCP Server |
| `oauth.FASTMCP_SERVER_AUTH_CLIENT_SECRET` | `str` | No | OAuth client secret for the MCP Server |
| `oauth.FASTMCP_SERVER_AUTH_BASE_URL` | `str` | No | Public base URL of the MCP Server |
| `oauth.FASTMCP_SERVER_AUTH_AUDIENCE` | `str` | No | OAuth audience value expected by the server |
| `oauth.FASTMCP_SERVER_AUTH_SCOPE` | `str` | No | OAuth scopes requested for client access |
| `oauth.user_impersonation` | `bool` | No | Controls whether the authenticated user identity is forwarded to the database |

---

## Starting the Server

Once your configuration file is ready, start the Analytics Engine MCP Server container and mount the file into the container as `/app/conf.json`.

Example:

```bash
docker run -d \
	-v $(pwd)/conf.json:/app/conf.json:ro \
	actian/analytics-engine-mcp-server:1.0.0
```

This example assumes:

- your local configuration file is named `conf.json`
- the container image reads its configuration from `/app/conf.json`

The container image starts the server with `/app/conf.json`, so the mounted file path inside the container should remain `/app/conf.json`.

After the container starts, connect your MCP client to the exposed server endpoint using the transport configured for your deployment.

---

## What Users Should Expect

Once the container is running and connected to Analytics Engine, an MCP client can discover the available server capabilities automatically.

In practice, this means a user can ask the client to:

- inspect database structure before writing a query
- run a read-only query and summarize the results
- look up details for a specific table
- review available database functions

This keeps Analytics Engine access available through a consistent MCP workflow while the server manages the database connection and response formatting.

---

## Next Steps

- [Tools](tools/index.md) — Learn about Analytics Engine tools
- [Resources](resources/index.md) — Learn about Analytics Engine resources
- [Prompts](prompts/index.md) — Learn about Analytics Engine prompts
