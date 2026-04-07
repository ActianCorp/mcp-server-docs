---
title: Get Started
description: Get the Actian MCP Server running in your environment with Docker.
---

# Get started

The Actian MCP Server is distributed as Docker container images — one image per supported Actian database. This page walks you through the steps to get a server running and connected to an MCP client.

## Prerequisites

- **Docker** (or Podman)
- Network access to an Actian database (Analytics Engine, Ingres, HCL Informix®, Zen, or NoSQL)
- An MCP-compatible AI client (Claude Desktop, Cursor, GitHub Copilot, Codex, or any MCP client)

## Step 1: Choose your database image

Each Actian database has its own container image with the required drivers pre-installed:

| Database | Container image |
|----------|----------------|
| Analytics Engine | [`actian/analytics-engine-mcp-server`](https://hub.docker.com/r/actian/analytics-engine-mcp-server) |
| Ingres | [`actian/ingres-mcp-server`](https://hub.docker.com/r/actian/ingres-mcp-server) |
| HCL Informix® | [`actian/informix-mcp-server`](https://hub.docker.com/r/actian/informix-mcp-server) |
| Zen | [`actian/zen-mcp-server`](https://hub.docker.com/r/actian/zen-mcp-server) |
| NoSQL | [`actian/nsql-mcp-server`](https://hub.docker.com/r/actian/nsql-mcp-server) |

## Step 2: Create a configuration file

Create a `conf.json` file with the connection details for your database. Each database has its own configuration format — see the database-specific page for the full field reference:

- [Analytics Engine configuration](../analytics_engine/index.md#configuration)
- [Zen configuration](../zen/index.md#configuration)
- [Ingres configuration](../ingres/index.md#configuration)
- [HCL Informix® configuration](../informix/index.md#configuration)
- [NoSQL configuration](../nosql/index.md#configuration)

All database configurations share these common fields for the MCP server:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `database_user` | `str` | Yes | Database username. |
| `database_password` | `str` | Yes | Database password. |
| `host` | `str` | Yes | Host address the MCP server listens on inside the container. |
| `port` | `str` | Yes | Port the MCP server listens on inside the container. |
| `ssl_certfile` | `str` | No | Path to the TLS certificate file. |
| `ssl_keyfile` | `str` | No | Path to the TLS private key file. |
| `oauth` | `object` | No | OAuth 2.0 configuration. See [Authentication](../authentication/index.md). |

!!! warning "Protect your configuration file"
    The configuration file contains database credentials. Set restrictive permissions on the host (`chmod 600 conf.json`) and avoid committing it to version control. The `:ro` flag in the mount command ensures the file cannot be modified from inside the container.

## Step 3: Start the container

Mount your configuration file into the container as `/app/conf.json`:

```bash
docker run -d \
    -v $(pwd)/conf.json:/app/conf.json:ro \
    -p 8000:8000 \
    actian/analytics-engine-mcp-server
```

Replace the image name with the one for your database.

## Step 4: Connect an MCP client

The server runs in **HTTP transport** mode. Clients connect to:

```
http://localhost:<port>/mcp
```

See [Connecting to MCP Clients](../mcp_clients/index.md) for configuration examples for Claude Desktop, Cursor, GitHub Copilot, fast-agent, and Codex.

## Step 5: Verify the connection

Run through these three checks to confirm everything is working end-to-end.

**1. Container is running**
```bash
docker ps --filter "name=actian-mcp"
```

You should see the container with a status of `Up`.

**2. MCP endpoint is reachable**
```bash
curl -i http://localhost:8000/mcp
```

Any response (not "connection refused") confirms the server is listening. A `200` or `307` status means it's ready.

**3. Test from your MCP client**

Open your configured MCP client. Ask:

> "List all tables in the database"

The client will invoke the `list_tables` tool. If you see table names returned, the full chain — client → server → database — is working.

For the complete list of available tools per database, see:

- [Analytics Engine tools](../analytics_engine/tools/index.md)
- [Ingres tools](../ingres/tools/index.md)
- [Zen tools](../zen/tools/index.md)
- [HCL Informix® tools](../informix/tools/index.md)
- [NoSQL tools](../nosql/tools/index.md)

## Optional: Add authentication

For deployments outside a trusted local environment, enable OAuth 2.0 authentication with Keycloak or Auth0:

- [Authentication overview](../authentication/index.md)
- [Keycloak setup](../authentication/keycloak/index.md)
- [Auth0 setup](../authentication/auth0/index.md)

## Next steps

<div class="grid cards" markdown>

- :material-connection: **[MCP clients](../mcp_clients/index.md)**  
  Configuration examples for Claude Desktop, Cursor, GitHub Copilot, and more.

- :material-shield-check: **[Authentication](../authentication/index.md)**  
  Secure your server with OAuth 2.0 and an external identity provider.

</div>