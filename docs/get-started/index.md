---
title: Get Started
description: Choose your Actian database and set up the Actian MCP Server for it.
---

# Getting started with the Actian MCP Server

The Actian MCP Server connects an MCP-compatible AI client to an Actian database. It is
distributed as Docker container images, one per supported database. Each database has
its own image and its own configuration, so setup starts by picking yours.

## What you need

- **Container runtime**: Docker or Podman on the host machine
- **Database access**: network connectivity to a supported Actian database
- **AI client**: an MCP-compatible client such as Claude Desktop, Cursor, GitHub
  Copilot, or Codex

## How it works

Setting up any of the servers follows the same four steps. What differs per database is
the image, the configuration format, and the port.

1. **Configure** — write a configuration file with your connection details
2. **Start** — run the container with that file mounted
3. **Verify** — confirm the container is up and the endpoint answers
4. **Connect** — point your AI client at the server endpoint

## Which database do you have?

| Database | Container image | Configuration file | Default port | Set up |
|----------|----------------|--------------------|--------------|--------|
| Actian Ingres | [`actian/ingres-mcp-server`](https://hub.docker.com/r/actian/ingres-mcp-server) | `conf.json` | `8000` | [Set up Ingres](../ingres/index.md) |
| HCL Informix® | [`actian/informix-mcp-server`](https://hub.docker.com/r/actian/informix-mcp-server) | `conf.json` | `8000` | [Set up HCL Informix®](../hcl-informix/index.md) |
| Actian Zen | [`actian/zen-mcp-server`](https://hub.docker.com/r/actian/zen-mcp-server) | `conf.json` | `8000` | [Set up Zen](../zen/index.md) |
| Actian Analytics Engine | [`actian/analytics-engine-mcp-server`](https://hub.docker.com/r/actian/analytics-engine-mcp-server) | `conf.json` | `8000` | [Set up Analytics Engine](../analytics-engine/index.md) |
| Actian NoSQL | [`actian/nsql-mcp-server`](https://hub.docker.com/r/actian/nsql-mcp-server) | `application.properties` | `8080` | [Set up NoSQL](../nosql/index.md) |

!!! info "One server per database"
    Each database needs its own server instance, which means one server, one database,
    and one MCP endpoint. To reach two databases, run two containers.

## After the server is running

Your database's setup page ends with a running, verified server. These apply to all of
them:

<div class="grid cards" markdown>

- :material-connection: **[Connect a client](../mcp-clients/index.md)**
  Configuration examples for Claude Desktop, Cursor, GitHub Copilot, Codex, and
  fast-agent.

- :material-shield-check: **[Secure the server](../authentication/index.md)**
  OAuth 2.0 with an external identity provider, and TLS for remote deployments.

- :material-database-edit: **[Write support](../write-support/index.md)**
  Allow `INSERT`, `UPDATE`, and `DELETE`, gated by an OAuth scope and human approval.

- :material-puzzle: **[Extensions](../extensions/index.md)**
  Add your own tools, resources, and prompts in Python.

</div>
