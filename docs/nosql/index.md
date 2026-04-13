---
title: Actian NoSQL Database
description: Use the Actian MCP Server to connect MCP clients to Actian NoSQL Databases.
---

# Actian NoSQL Database

This section describes how to use the **Actian MCP Server** with **Actian NoSQL Database**.

## Overview

The Actian NoSQL MCP Server acts as a bridge between any MCP client and your Actian NoSQL Database. Once configured, clients can explore schema metadata, run read-only JPQL queries and access all details of the persistent objects retrieved.

### Capabilities

| Action | Description |
|--------|-------------|
| **Discover the Schema of a NoSQL Database** | List classes, Explore details of persistent classes. |
| **Run queries on database objects** | Use Filter, Projections, Navigation. |
| **Retrieve Objects by ID** | Including optimizations for collections of Object IDs. |

## Configuration

All configuration is provided as **environment variables** to the container. There is no configuration file.

### NoSQL Connection

| Environment Variable | Required | Description |
|----------------------|----------|-------------|
| `NSQL_CONNECTIONURL` | Yes | Connection URL in the format `database@server:port#user:password`. `port`, `user`, and `password` are optional. |

### Quarkus Properties

The server is a **Quarkus** application. Any standard Quarkus configuration property can be passed as an environment variable using `SCREAMING_SNAKE_CASE` notation. Some commonly used properties:

| Property | Environment Variable | Default | Description |
|----------|---------------------|---------|-------------|
| `quarkus.http.port` | `QUARKUS_HTTP_PORT` | `8080` | HTTP listening port. |
| `quarkus.http.ssl-port` | `QUARKUS_HTTP_SSL_PORT` | `8443` | HTTPS listening port. |

!!! note "Securing the server"
    To enable OAuth 2.0 or HTTPS, additional environment variables are required. See [Authentication](authentication/index.md) for the full configuration reference.

## Start the Server

Pass configuration as environment variables using `-e` flags. Any property from the [Configuration](#configuration) section can be included this way:

```bash
docker run --name NSQL-MCP \
  -e NSQL_CONNECTIONURL=<connection-url> \
  -e <ENV_VAR>=<value> \
  -p <host-port>:<container-port> \
  actian/nsql-mcp-server:1.0.0
```

A minimal example connecting to a local `cars` database on the default port:

```bash
docker run --name NSQL-MCP \
  -e NSQL_CONNECTIONURL=cars@localhost \
  -p 8080:8080 \
  actian/nsql-mcp-server:1.0.0
```


---

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](tools/index.md)**  
  Explore the available MCP tools for NoSQL database operations.

- :material-folder-open: **[Resources](resources/index.md)**  
  Learn about schema metadata resources.

- :material-chat-processing: **[Prompts](prompts/index.md)**  
  Discover pre-built prompt templates for common workflows.

- :material-lock: **[Authentication](authentication/index.md)**  
  Configure OAuth 2.0 and TLS for the NoSQL MCP Server.

</div>