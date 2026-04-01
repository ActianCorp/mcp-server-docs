---
title: Get Started
description: Get the Actian MCP Server running in your environment with Docker.
---

# Get started

The Actian MCP Server is distributed as Docker container images — one image per supported Actian database. This page walks you through the steps to get a server running and connected to an MCP client.

## Prerequisites

- **Docker** (or Podman)
- Network access to an Actian database (Analytics Engine, Ingres, Informix, Zen, or NoSQL)
- An MCP-compatible AI client (Claude Desktop, Cursor, GitHub Copilot, Codex, or any MCP client)

## Step 1 — Choose your database image

Each Actian database has its own container image with the required drivers pre-installed:

| Database | Container image |
|----------|----------------|
| Analytics Engine | [`actian/analytics-engine-mcp-server`](https://hub.docker.com/r/actian/analytics-engine-mcp-server) |
| Ingres | [`actian/ingres-mcp-server`](https://hub.docker.com/r/actian/ingres-mcp-server) |
| Informix | [`actian/informix-mcp-server`](https://hub.docker.com/r/actian/informix-mcp-server) |
| Zen | [`actian/zen-mcp-server`](https://hub.docker.com/r/actian/zen-mcp-server) |
| NoSQL | [`actian/nsql-mcp-server`](https://hub.docker.com/r/actian/nsql-mcp-server) |

## Step 2 — Create a configuration file

Create a `conf.json` file with the connection details for your database. Each database has its own configuration format — see the database-specific page for the full field reference:

- [Analytics Engine configuration](../analytics_engine/index.md#configuration)
- [Zen configuration](../zen/index.md#configuration)
- [Ingres configuration](../ingres/index.md#configuration)
- [Informix configuration](../informix/index.md#configuration)
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

## Step 3 — Start the container

Mount your configuration file into the container as `/app/conf.json`:

```bash
docker run -d \
    -v $(pwd)/conf.json:/app/conf.json:ro \
    -p 8000:8000 \
    actian/analytics-engine-mcp-server
```

Replace the image name with the one for your database.

## Step 4 — Connect an MCP client

The server runs in **HTTP transport** mode. Clients connect to:

```
http://localhost:<port>/mcp
```

See [Connecting to MCP Clients](../mcp_clients/index.md) for configuration examples for Claude Desktop, Cursor, GitHub Copilot, fast-agent, and Codex.

## Step 5 — Verify the connection

**Check the container is running:**

```bash
docker ps
```

You should see your container listed with a status of `Up`.

**Check the MCP endpoint is reachable:**

```bash
curl -s http://localhost:8000/mcp
```

A response (rather than "connection refused") confirms the server is listening.

**Test from your MCP client:**

Open your MCP client (configured in Step 4). The client should detect the Actian MCP Server and list its available tools. Ask a question like:

> "List all tables in the database"

The client will invoke the server's `list_tables` tool. If you see table names, the full chain — client, server, and database — is working.

For the complete list of available tools per database, see:

- [Analytics Engine tools](../analytics_engine/tools/index.md)
- [Ingres tools](../ingres/tools/index.md)
- [Zen tools](../zen/tools/index.md)
- [Informix tools](../informix/tools/index.md)
- [NoSQL tools](../nosql/tools/index.md)

## Optional — Add authentication

For deployments outside a trusted local environment, enable OAuth 2.0 authentication with Keycloak or Auth0:

- [Authentication overview](../authentication/index.md)
- [Keycloak setup](../authentication/keycloak/index.md)
- [Auth0 setup](../authentication/auth0/index.md)

## Next steps

- [Connecting to MCP Clients](../mcp_clients/index.md) — Client configuration for Claude Desktop, Cursor, and more
- [Authentication](../authentication/index.md) — Secure your deployment with OAuth 2.0
