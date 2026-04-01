---
title: Informix
description: Use the Actian MCP Server to connect MCP clients to Informix Database.
---
# Informix

This page explains how to use the Actian MCP Server with Informix Database.

When configured for Informix, the server gives an MCP-compatible client a simple way to explore schema information and run read-only database queries through a standard interface.

## What you can do
With the Informix database server, AI clients can:

- Run read-only SQL queries.
- List available tables and views.
- Inspect the structure of a specific table.
- Read database schema metadata.
- List user-defined functions and procedures.

## Configuration

When the server is provided as a Docker container, the main user-provided input is a JSON configuration file that's mounted into the container.

The MCP Server container starts the MCP Server in HTTP transport mode, so the configuration should include the network settings that the container will use.

Create a file such as `conf.json` with the following structure:

```json
{
    "servername": "(str) <server_name>",
    "service": "(int) <service_port>",
    "dsn": "(str) <dsn_name>",
    "server": "(str)<database_host>",
    "database": "(str)<database_name>",
    "database_user": "(str)<database_user>",
    "database_password": "(str)<database_password>",
    "max_connections": "(int)<max_concurrent_connections_to_database>",
    "max_rows": "(int, optional, default 1000)<max_number_of_rows_to_retrieve_from_database>",
    "host": "(str)<mcp_server_host>",
    "port": "(int)<mcp_server_port>",
    "database_user": "<database_user>",
	"database_password": "<database_password>",
    "ssl_certfile": "(str, optional)<path_to_ssl_certificate_file>",
    "ssl_keyfile": "(str, optional)<path_to_ssl_private_key_file>",
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
| `servername` | `str` | Yes | Informix database server name. |
| `service` | `int` | Yes | Informix server port number. |
| `dsn` | `str` | Yes | Data source name. |
| `server` | `str` | Yes | Host address for the Informix database. |
| `database` | `str` | Yes | Name of the database that the MCP Server connects to. |
| `max_connections` | `int` | Yes | Maximum number of concurrent database connections the server keeps in its pool. |
| `max_rows` | `int` | No | Maximum number of rows returned for a single query response. Defaults to `1000`. |
| `host` | `str` | Yes | Host address that the MCP Server listens on inside the container. |
| `port` | `str` | Yes | Port that the MCP Server listens on inside the container. |
| `database_user` | `str` | Yes | Database username, can also be provided on the command line. |
| `database_password` | `str` | Yes | Database password, can also be provided on the command line. |
| `ssl_certfile` | `str` | No | Path to the TLS certificate file. |
| `ssl_keyfile` | `str` | No | Path to the TLS private key file. |
| `oauth` | `object` | No | OAuth configuration block for protected MCP server deployments. See [The `oauth` configuration block](../authentication/index.md#the-oauth-configuration-block) for the required fields. |

## Starting the server

Once your configuration file is ready, start the Actian MCP Server container and mount the file into the container as `/app/conf.json`.

Example:

```bash
podman run --network host --rm -it \
  -v $(pwd)/conf_temp.json:/app/conf.json:ro,Z \
  actian/informix-mcp-server-linux:1.0.0 bash
```

This example assumes:

- Your local configuration file is named `conf.json`.
- The container image reads its configuration from `/app/conf.json`.

The container image starts the server with `/app/conf.json`, so the mounted file path inside the container should remain `/app/conf.json`.

After the container starts, connect your MCP client to the exposed server endpoint using the transport configured for your deployment.

Inside the container, run `cd /app`, then start the server with the following command:

```bash
actian-mcp-server --dbms=informix --transport=sse --conf-file=/app/conf.json --username=USERNAME --password=PASSWORD
```

## What you can expect

Once the container is running and connected to Informix database, your MCP client can discover the available server capabilities automatically.

In practice, you can ask the client to:

- Inspect database structure before writing a query.
- Run a read-only query and summarize the results.
- Look up details for a specific table.
- Review available database functions.

The server manages the database connection and response formatting so you can focus on your queries.

## Next steps

- [Tools](tools/index.md) — Learn about Informix MCP server tools
- [Resources](resources/index.md) — Learn about Informix MCP server resources
- [Prompts](prompts/index.md) — Learn about Informix MCP server prompts