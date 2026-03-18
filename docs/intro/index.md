---
title: Introduction
description: An overview of the Actian MCP Server — what it is, how it works, and key concepts.
---

# Introduction to Actian MCP Server

The **Actian MCP Server** is an open, extensible server that implements the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) to connect AI language models with Actian data sources and services.

It provides a structured way for AI agents and LLM-based applications to discover, query, and interact with Actian databases and analytics engines through a well-defined protocol.

---

## What is MCP?

The **Model Context Protocol (MCP)** is an open standard that defines how AI models communicate with external tools, data sources, and services. MCP servers expose three primitives that AI clients can consume:

| Primitive | Description |
|-----------|-------------|
| **Tools** | Callable functions the AI can invoke (e.g., run a SQL query) |
| **Resources** | Readable data sources the AI can access (e.g., schema information) |
| **Prompts** | Pre-built prompt templates for common workflows |

---

## What Does the Actian MCP Server Do?

The Actian MCP Server acts as a bridge between your AI client (such as Claude, Cursor, or any MCP-compatible agent) and Actian data products including:

- **Actian Zen** — Embedded relational database engine
- **Actian Analytics Engine** — High-performance analytics

It handles authentication, connection management, multi-tenancy, and exposes database operations as MCP-native tools and resources.

---

## Key Features

- **Plugin architecture** — Extend the server with custom plugins for any Actian product
- **Multi-tenancy** — Serve multiple tenants from a single server instance
- **OAuth 2.0 support** — Secure authentication for MCP clients
- **Transport flexibility** — Supports `stdio` and SSE transports
- **Read-only mode** — Restrict AI agents to read-only database operations
- **Schema introspection** — AI agents can explore database schemas automatically

---

## Architecture Overview

```
┌─────────────────────┐        MCP Protocol        ┌─────────────────────────┐
│   AI Client / Agent │ ◄──────────────────────────► │  Actian MCP Server      │
│  (Claude, Cursor…)  │                              │  ┌─────────────────┐   │
└─────────────────────┘                              │  │  Plugin Layer   │   │
                                                     │  │  - Zen Plugin   │   │
                                                     │  │  - Analytics    │   │
                                                     │  │  - Custom…      │   │
                                                     │  └────────┬────────┘   │
                                                     └───────────┼─────────────┘
                                                                 │
                                                     ┌───────────▼─────────────┐
                                                     │   Actian Data Sources   │
                                                     │  (Zen DB, Analytics…)   │
                                                     └─────────────────────────┘
```

---

## Next Steps

- [Get Started](../get_started/index.md) — Install and run your first MCP server
- [Develop with MCP](../develop_with_mcp/index.md) — Build tools, resources, and plugins
- [Configuration](../configuration/index.md) — Configure the server for your environment
