---
title: Actian NoSQL Database
description: Use the Actian MCP Server to connect MCP clients to Actian NoSQL Databases.
---

# Actian NoSQL Database

Connect your MCP-compatible client to **Actian NoSQL Database** using the Actian MCP Server. Once configured, clients can explore schema metadata, run read-only JPQL queries, and access all details of the persistent objects retrieved.

## Overview

The Actian MCP Server acts as a bridge between any MCP client and your Actian NoSQL Database. It handles connection management, schema discovery, and query execution, so you can focus on exploring your data.

### Capabilities

| Action | Description |
|--------|-------------|
| **Discover the schema** | List all classes and explore their fields and inheritance hierarchy. |
| **Run JPQL queries** | Execute read-only queries against your database. |
| **Retrieve objects by ID** | Fetch one or many objects directly by LOID for the fastest retrieval path. |

## Prerequisites

- Docker installed and running.
- Access credentials for your Actian NoSQL database
- (Optional) TLS certificate and key files for secure deployments.
- (Optional) An OIDC provider if using OAuth authentication.

## Configuration

The server is distributed as a Docker container. All configuration is provided through an `application.properties` file mounted into the container at `/home/jboss/config/application.properties`. Environment variables are supported as an alternative — any property can be passed with a `-e` flag using `SCREAMING_SNAKE_CASE` notation, and they take precedence over the file.

### NoSQL Connection

| Property | Required | Description |
|----------|----------|-------------|
| `nsql_connectionURL` | Yes | Connection URL in the format `database@server:port#user:password`. `port`, `user`, and `password` are optional. |

### Quarkus Properties

The server is a **Quarkus** application. Any standard Quarkus configuration property can be set in `application.properties`. Some commonly used properties:

| Property | Default | Description |
|----------|---------|-------------|
| `quarkus.http.port` | `8080` | HTTP listening port. |
| `quarkus.http.ssl-port` | `8443` | HTTPS listening port. |
| `quarkus.log.level` | `INFO` | Root log level. Individual categories can be tuned independently — for example, `quarkus.log.category."io.quarkus.oidc".level=DEBUG`. See the [Quarkus logging guide](https://quarkus.io/guides/logging#configure-the-log-level-category-and-format) for the full reference. |

!!! note "Securing the server"
    To enable OAuth 2.0 or HTTPS, additional properties are required. See [Authentication](authentication/index.md) for the full configuration reference.

## Start the Server

Add your settings to `application.properties` and mount it into the container:

```properties
nsql_connectionURL=<connection-url>
```

```bash
docker run --name NSQL-MCP \
  -v /path/to/application.properties:/home/jboss/config/application.properties:ro \
  -p <host-port>:<container-port> \
  actian/nsql-mcp-server:1.0.0
```

Once the container is running, connect your MCP client to the exposed server endpoint using the host and port from your configuration.

---

## Next Steps

<div class="grid cards" markdown>

- :material-lock: **[Authentication](authentication/index.md)**  
  Configure OAuth 2.0 and TLS for the Actian MCP Server with Actian NoSQL Database.

- :material-tools: **[Tools](tools/index.md)**  
  Explore the available MCP tools for NoSQL database operations.

- :material-folder-open: **[Resources](resources/index.md)**  
  Learn about schema metadata resources.

- :material-chat-processing: **[Prompts](prompts/index.md)**  
  Discover pre-built prompt templates for common workflows.

</div>