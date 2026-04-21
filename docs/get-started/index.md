---
title: Get Started
description: Get the Actian MCP Server running in your environment with Docker.
---

# Getting Started with Actian MCP Server

The Actian MCP Server is distributed as Docker container images, with one dedicated image for each supported Actian database. This guide explains the process of starting the server instance and connecting it to an MCP-compatible artificial intelligence (AI) client.

## Prerequisites

Before you begin, ensure that the following requirements are met:

- **Container runtime**: Docker or Podman is installed on the host machine
- **Database access**: There is network connectivity to a supported Actian database (Ingres, HCL Informix®, Zen, NoSQL, or Analytics Engine).
- **AI client**: An MCP-compatible client, such as Claude Desktop, Cursor, GitHub Copilot, or Codex already exists.

## Step 1: Select a Database Image

Each Actian database uses a specific container image that is preconfigured with the required drivers. Identify the correct image for the environment:

| Database | Container image |
|----------|----------------|
| Ingres | [`actian/ingres-mcp-server`](https://hub.docker.com/r/actian/ingres-mcp-server) |
| HCL Informix® | [`actian/informix-mcp-server`](https://hub.docker.com/r/actian/informix-mcp-server) |
| Zen | [`actian/zen-mcp-server`](https://hub.docker.com/r/actian/zen-mcp-server) |
| NoSQL | [`actian/nsql-mcp-server`](https://hub.docker.com/r/actian/nsql-mcp-server) |
| Analytics Engine | [`actian/analytics-engine-mcp-server`](https://hub.docker.com/r/actian/analytics-engine-mcp-server) |

## Step 2: Create a Configuration File

For most databases, you need to create a `conf.json` file that contains the specific connection details.

Each database has unique settings. For more information, see the database configuration document:

- [Ingres Configuration](../ingres/index.md#configuration)
- [HCL Informix® Configuration](../hcl-informix/index.md#configuration)
- [Zen Configuration](../zen/index.md#configuration)
- [NoSQL Configuration](../nosql/index.md#configuration)
- [Analytics Engine Configuration](../analytics-engine/index.md#configuration)

All database configurations except NoSQL share the following standard MCP server fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `database_user` | String | Yes | Database username |
| `database_password` | String | Yes | Database password |
| `host` | String | Yes | Host address the MCP server listens to in the container |
| `port` | String | Yes | Port the MCP server listens to in the container. |
| `ssl_certfile` | String| No | Path to the TLS certificate file. In the container, this is always mapped to `/app/server.crt`. |
| `ssl_keyfile` | String | No | Path to the TLS private key file. In the container, this is always mapped to `/app/server.key`. |
| `log_level` | String | No | Server log verbosity. Valid values: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. Defaults to `INFO`. |
| `oauth` | Object | No | OAuth 2.0 configuration settings for authentication. For more information, see [Authentication Guide](../authentication/index.md).|

!!! note "Configuration File Protection"
    The configuration file contains database credentials. Set restrictive permissions on the host (`chmod 600 conf.json`) and avoid committing it to version control.

## Step 3: Start the Container

!!! warning "Actian NoSQL users"
    The Actian MCP Server for Actian NoSQL Database uses a different startup command. See [Start the Server](../nosql/index.md#start-the-server) for the NoSQL-specific steps.

To start the server, run the container and mount the configuration file to `/app/conf.json`. Use the `:ro` (read-only) flag in the `mount` command to ensure that the configuration file cannot be modified from inside the container.

Run the following command (replace the image name with the database image as per Step 1): 

!!! note "Analytics Engine example"
    The following example demonstrates how to start the Analytics Engine server.

```bash
docker run -d \
    -v $(pwd)/conf.json:/app/conf.json:ro \
    -p 8000:8000 \
    actian/analytics-engine-mcp-server
```

## Step 4: Connect to an MCP Client

The server operates in HTTP transport mode. Configure the AI client to connect to the following endpoint:

```
http://localhost:<port>/mcp
```
For example, if you mapped port 8000 in the previous step, the endpoint is `http://localhost:8000/mcp`.

For configuration examples for Claude Desktop, Cursor, GitHub Copilot, fast-agent, and Codex, see [Connecting MCP Clients](../mcp-clients/index.md).


## Step 5: Verify the Connection

Follow these steps to confirm that the server is running and successfully communicating with the database and AI client:

**1. Verify the container status**

Run the following command to ensure that the container is actively running:

```bash
docker ps --filter "name=actian-mcp"
```

Confirm that the container status is `Up`.

**2. Verify the endpoint**

Ping the server to confirm that it is listening for requests:

```bash
curl -i http://localhost:<port>/mcp
```

If the server is ready, it returns a `200` or `307` status code instead of a `connection refused` error.

**3. Test the client integration**

Open the configured MCP client. It automatically detects the Actian MCP Server and displays its available tools.
Prompt the AI with a standard database request, such as:

> "List all tables in the database"

The client will invoke the server's `list_tables` tool. If the AI client returns a list of the database tables, the end-to-end connection is working correctly.

For the complete list of available tools for each database, see database-specific documentation:

- [Ingres tools](../ingres/tools/index.md)
- [HCL Informix® tools](../hcl-informix/tools/index.md)
- [Zen tools](../zen/tools/index.md)
- [NoSQL tools](../nosql/tools/index.md)
- [Analytics Engine tools](../analytics-engine/tools/index.md)

## Step 6 (Optional): Add Authentication

If you are deploying the server outside a secure, trusted local environment, it is recommended to use OAuth 2.0 authentication. You can secure the server using an external identity provider like Keycloak or Auth0. See the following authentication documentation for detailed setup instructions:

- [Authentication overview](../authentication/index.md)
- [Keycloak setup](../authentication/keycloak/index.md)
- [Auth0 setup](../authentication/auth0/index.md)

## Next Steps

<div class="grid cards" markdown>

- :material-connection: **[MCP clients](../mcp-clients/index.md)**  
  Configuration examples for Claude Desktop, Cursor, GitHub Copilot, and fast-agent.

- :material-shield-check: **[Authentication](../authentication/index.md)**  
  Secure the server with OAuth 2.0 and an external identity provider.

</div>
