---
title: Actian Ingres
description: Use the Actian MCP Server to connect MCP clients to Actian Ingres.
---

# Actian Ingres

This page explains how to use the **Actian MCP Server** with **Actian Ingres**.

When configured for Ingres, the server gives an MCP-compatible client a simple way to explore schema information and run read-only database queries through a standard interface.

## What you can do

With the Ingres server, AI clients can:

- Run **read-only SQL queries**.
- List available tables and views.
- Inspect the structure of a specific table.
- Read database schema metadata.
- List user-defined functions and procedures.

## Configuration

When the server is provided as a Docker container, the main user-provided input is a JSON configuration file that's mounted into the container.

The Ingres container starts the MCP Server in **HTTP transport** mode, so the configuration should include the network settings that the container will use.

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
| `driver` | `str` | Yes | ODBC driver name used to connect to Ingres. |
| `server` | `str` | Yes | Host or connection target for the Ingres database. |
| `database` | `str` | Yes | Name of the database that the MCP Server connects to. |
| `max_connections` | `int` | Yes | Maximum number of concurrent database connections the server keeps in its pool. |
| `max_rows` | `int` | No | Maximum number of rows returned for a single query response. Defaults to `1000`. |
| `host` | `str` | Yes | Host address that the MCP Server listens on inside the container. |
| `port` | `str` | Yes | Port that the MCP Server listens on inside the container. |
| `database_user` | `str` | Yes | Database username. |
| `database_password` | `str` | Yes | Database password. |
| `ssl_certfile` | `str` | No | Path to the TLS certificate file. |
| `ssl_keyfile` | `str` | No | Path to the TLS private key file. |
| `oauth` | `object` | No | OAuth configuration block for protected MCP server deployments. See [The `oauth` configuration block](../authentication/index.md#the-oauth-configuration-block) for the required fields. |

## Starting the server

Once your configuration file is ready, start the Ingres MCP Server container and mount the file into the container as `/app/conf.json`.

Example:

```bash
docker run -d \
	-v $(pwd)/conf.json:/app/conf.json:ro \
	actian/ingres-mcp-server:1.0.0
```

This example assumes:

- Your local configuration file is named `conf.json`.
- The container image reads its configuration from `/app/conf.json`.

The container image starts the server with `/app/conf.json`, so the mounted file path inside the container should remain `/app/conf.json`.

After the container starts, connect your MCP client to the exposed server endpoint using the transport configured for your deployment.

## What users should expect

Once the container is running and connected to Ingres, an MCP client can discover the available server capabilities automatically.

In practice, this means a user can ask the client to:

- Inspect database structure before writing a query.
- Run a read-only query and summarize the results.
- Look up details for a specific table.
- Review available database functions.

This keeps Ingres access available through a consistent MCP workflow while the server manages the database connection and response formatting.

## Next steps

- [Tools](tools/index.md) — Learn about Ingres tools
- [Resources](resources/index.md) — Learn about Ingres resources
- [Prompts](prompts/index.md) — Learn about Ingres prompts
