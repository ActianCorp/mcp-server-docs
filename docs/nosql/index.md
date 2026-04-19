---
title: Actian NoSQL Database
description: Use the Actian MCP Server to connect MCP clients to Actian NoSQL Databases.
---

# Actian NoSQL MCP Server

The Actian MCP Server connects your MCP clients to an Actian NoSQL database. Once configured, you can use the server to browse schema metadata, execute JPQL queries, and manage persistent objects.

### Capabilities

Use the MCP Server to perform the following tasks:

| Action | Description |
|--------|-------------|
| **Discover the Schema of a NoSQL Database** | List classes and explore the details of persistent classes. |
| **Run queries on database objects** | Filter database objects, use projections, and navigate data. |
| **Retrieve Objects by ID** | Fetch objects by ID, including optimized support for Object ID collections. |

## Configuration

The container uses environment variables for all configuration settings. There is no physical configuration file to manage.

### NoSQL Connection

| Environment Variable | Required | Description |
|----------------------|----------|-------------|
| `NSQL_CONNECTIONURL` | Yes | Use the Connection URL in this format `database@server:port#user:password`. Note: `port`, `user`, and `password` are optional. |

### Quarkus Properties

The server is a **Quarkus** application, you can pass any standard Quarkus property as an environment variable using `SCREAMING_SNAKE_CASE`. Following are the commonly used properties:

| Property | Environment Variable | Default | Description |
|----------|---------------------|---------|-------------|
| `quarkus.http.port` | `QUARKUS_HTTP_PORT` | `8080` | HTTP listening port. |
| `quarkus.http.ssl-port` | `QUARKUS_HTTP_SSL_PORT` | `8443` | HTTPS listening port. |

!!! note "Securing the server"
    To enable OAuth 2.0 or HTTPS, additional environment variables are required, see [Authentication](authentication/index.md) for the full configuration reference.

## Start the Server

To start the server, use the `-e` flag to pass the configuration as environment variables. You can include any property listed in the [Configuration](#configuration) section in this manner:

#### Basic Docker Command:

```bash
docker run --name NSQL-MCP \
  -e NSQL_CONNECTIONURL=<connection-url> \
  -e <ENV_VAR>=<value> \
  -p <host-port>:<container-port> \
  actian/nsql-mcp-server:1.0.0
```

**Example: Connecting to a local "cars" database**

This example connects to a local database on the default port (8080):

```bash
docker run --name NSQL-MCP \
  -e NSQL_CONNECTIONURL=cars@localhost \
  -p 8080:8080 \
  actian/nsql-mcp-server:1.0.0
```


## Next Steps

<div class="grid cards" markdown>

- :material-lock: **[Authentication](authentication/index.md)**  
  Configure OAuth 2.0 and TLS for the NoSQL MCP Server.

- :material-tools: **[Tools](tools/index.md)**  
  Explore the available MCP tools for NoSQL database operations.

- :material-folder-open: **[Resources](resources/index.md)**  
  Learn more about schema metadata resources.

- :material-chat-processing: **[Prompts](prompts/index.md)**  
  Use pre-built prompt templates for common workflows.

</div>