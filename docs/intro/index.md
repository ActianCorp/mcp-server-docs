---
title: Introduction
description: A simple overview of the Actian MCP Server, its purpose, and the core concepts behind it.
---

# Actian MCP Server

The Actian [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) Server connects artificial intelligence (AI) applications to the Actian databases. By implementing the open-source MCP, the server acts as a secure bridge between an MCP-compatible AI client and the data source. It eliminates the need for custom integrations, allowing AI agents to discover capabilities, access metadata, and safely run database tasks through a standardized connection.

MCP is an open standard designed to connect AI models with external systems, tools, and data sources. When you use an Actian MCP Server, it provides the AI clients with three core building blocks:

| Component | Description | Example | 
|-----------|-------------|---------|
| **Tools** | Callable functions that the AI can invoke| Running a specific SQL query |
| **Resources** | Read-only data sources that the AI can access| Viewing database schema information |
| **Prompts** |Prebuilt templates designed for recurring tasks| Reusing common database workflows |

## MCP Server Capabilities 

You can use the Actian MCP Server to provide a single and unified interface for the Actian database management systems instead of building and maintaining separate connections for every AI client or workflow.

Depending on the configuration, the server enables AI clients to:

- Run database queries using MCP tools.
- Discover tables and other database objects.
- Review schema details and metadata.
- Use reusable prompts for database-oriented tasks.

The server also manages backend requirements, including transport, configuration, authentication, and secure database access.

## Architecture and Request Flow

### Workflow

The Actian MCP Server sits between AI clients and the databases that they need to access.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'fontSize': '12px', 'fontFamily': 'arial'}}}%%
flowchart TB
    subgraph Clients["MCP Clients"]
        claude["Claude Desktop"]
        cursor["Cursor"]
        copilot["GitHub Copilot"]
        fastagent["fast-agent"]
        codex["Codex"]
        custom["Custom AI Agents"]
    end

    subgraph Transport["Transport Layer"]
        http["HTTP / SSE
(Network)"]
    end

    subgraph Auth["Authentication"]
        idp["Identity Provider
(Keycloak / Auth0)"]
        oauth["OAuth 2.0 / OIDC
JWT Validation"]
    end

    subgraph MCP["Actian MCP Server"]
        direction TB
        core["MCP Protocol Handler"]
        tools["Tools
─────────────
• Run SQL Queries
• List Tables & Views
• Describe Table Schema
• List Functions"]
        resources["Resources
─────────────
• Schema Metadata
• Table Definitions"]
        plugins["Database Plugins"]
        pool["Connection Pool
(ODBC)"]
    end

    subgraph Databases["Actian Databases"]
        ae["Analytics Engine"]
        ingres["Ingres"]
        zen["Zen"]
        informix["HCL Informix®"]
        nosql["NoSQL"]
    end

    subgraph Security["Security Controls"]
        readonly["Read-only Mode"]
        impersonation["User Impersonation
(SET SESSION AUTHORIZATION)"]
        tls["TLS / HTTPS"]
    end

    claude & cursor & copilot & fastagent & codex & custom --> http

    http --> oauth
    oauth <--> idp
    oauth --> core

    core --> tools & resources
    tools & resources --> plugins
    plugins --> pool

    pool --> ae & ingres & zen & informix & nosql

    Security -.-> MCP
```

### End-to-End Request Flow

When an AI agent interacts with the database, the system follows the standard sequence:

```mermaid
%%{init: {'theme': 'default', 'themeVariables': {'fontSize': '44px', 'fontFamily': 'arial'}}}%%
sequenceDiagram
    actor User
    participant Client as MCP Client (Claude/Cursor/Codex)
    participant Transport as HTTP / SSE Transport
    participant Auth as OAuth 2.0 (Keycloak/Auth0)
    participant Server as Actian MCP Server
    participant Plugin as Database Plugin
    participant DB as Actian Database (Analytics Engine/Ingres/Zen/HCL Informix®/NoSQL)

    User->>Client: Natural language query
    Client->>Transport: MCP request

    Transport->>Auth: Validate JWT token
    Auth-->>Transport: Token valid

    Transport->>Server: Forward request
    Server->>Server: Route to tool/resource

    opt User Impersonation enabled
        Server->>Plugin: SET SESSION AUTHORIZATION
    end

    Plugin->>DB: Execute read-only SQL (ODBC)
    DB-->>Plugin: Query results
    Plugin-->>Server: Formatted response
    Server-->>Transport: MCP response
    Transport-->>Client: Results
    Client-->>User: Natural language answer
```

## Key Features

<div class="grid cards" markdown>

- :material-connection: **MCP-Native Capabilities**  
  Exposes tools, resources, and prompts in a standard MCP format usable by any compatible client.

- :material-docker: **Container-Friendly Deployment**  
  Runs each DBMS server instance in its own container to ensure clean environment isolation.

- :material-shield-lock: **OAuth 2.0 Support**  
  Uses `OAuth 2.0` to provide secure, standards-based access for all MCP clients.

- :material-transit-connection-horizontal: **HTTP Transport**  
  Operates in `HTTP` transport mode to simplify network connectivity.

- :material-eye-lock: **Read-only Mode**  
  Restricts AI agents to read-only operations, preventing unintended modifications to the data.

- :material-database-search: **Schema Discovery**  
  Enables AI agents to review database structures and metadata before executing queries.

</div>

## MCP Server Deployment

You can deploy an MCP Server as follows:

<div class="steps-container" markdown>
<div class="step-item">
<h4 class="step-title">Configure the server</h4>
<p class="step-description">Start a server instance using a configuration that targets the specific Actian DBMS.</p>
</div>
<div class="step-item">
<h4 class="step-title">Connect to the database</h4>
<p class="step-description">The server connects to the target DBMS using an ODBC connection pool.</p>
</div>
<div class="step-item">
<h4 class="step-title">Use database capabilities</h4>
<p class="step-description">The server makes database tools, resources, and prompts available through the MCP protocol.</p>
</div>
<div class="step-item">
<h4 class="step-title">Connect to the AI client</h4>
<p class="step-description">An MCP-compatible client uses the database capabilities to query data, inspect metadata, and run workflows.</p>
</div>
</div>

!!! info 
    Each Actian DBMS requires its own dedicated Actian MCP Server instance, which means there is a single server, database, and MCP endpoint.

## MCP Server Advantages 

By removing the need to build individual integrations for every AI use case, the Actian MCP Server provides a standardized way to use the trusted database capabilities. It ensures that deployment and access control remain securely managed at the server layer.

## Next Steps

<div class="grid cards" markdown>

- :material-rocket-launch: **[Get Started](../get-started/index.md)**  
  To deploy Actian MCP Server instance and connect it to an AI client, see [Getting Started with MCP Server](../get-started/index.md).
</div>
