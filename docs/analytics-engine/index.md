---
title: Overview
description: Connect MCP clients to Actian Analytics Engine for schema exploration and SQL queries, with optional write support.
---

# Actian MCP Server for Analytics Engine

Connect the MCP-compatible client to the Actian Analytics Engine using the Actian MCP Server. With this setup, the client can explore schema metadata and run SQL queries through a standard interface. Queries are read-only unless you enable write mode. The server manages connection pooling, response formatting, and schema discovery automatically.

The Analytics Engine runs in two deployments, and the MCP Server supports both:

- **Self-hosted.** The Analytics Engine runs on your own infrastructure, on premises or in your own cloud environment, and you deploy the MCP Server alongside it.
- **SaaS.** The Analytics Engine powers the warehouse on the Actian Analytics AI Platform, and the MCP Server is configured for you.

The tools, resources, and prompts are the same in both deployments. Only the setup and the connection details differ.


## Deployment Options

### Self-Hosted

You run the MCP Server in a container alongside your own Analytics Engine instance. You supply the database connection details in `conf.json`, secure the endpoint, and manage the server lifecycle.

For detailed instructions, see [Self-Hosted](self-hosted.md).

### SaaS

The MCP Server is deployed and configured with the warehouse. There is nothing to install and no configuration file to write. The client connects to a URL specific to that warehouse and signs in with OAuth, and your existing database privileges apply to every query.

For detailed instructions, see [SaaS](saas.md).


## Capabilities

The Actian Analytics Engine MCP Server supports the following operations in both deployments:

| Action | Description |
|--------|-------------|
| **Execute SQL queries** | Execute read-only SQL against the database |
| **List tables and views** | Discover available objects in the schema |
| **Inspect table structure** | Retrieve column definitions and types |
| **Read schema metadata** | Explore database-level metadata |
| **List functions and procedures** | View available user-defined functions and procedures |
| **Execute write queries** | Run `INSERT`, `UPDATE`, `DELETE`, and `MERGE` statements. Off by default in a self-hosted deployment |

!!! note "Write support is opt-in"
    In a self-hosted deployment, the server permits only read queries unless you set `query_mode` to `read-write`. Each write then requires the `mcp:write` scope and human approval. For more information, see [Write support](write-support.md).


## Next Steps

<div class="grid cards" markdown>

- :material-server: **[Self-Hosted](self-hosted.md)**  
  Deploy and configure the server against your own Analytics Engine instance.

- :material-cloud: **[SaaS](saas.md)**  
  Connect to a warehouse on the Actian Analytics AI Platform.

- :material-tools: **[Tools](tools/index.md)**  
  Learn more about the Analytics Engine tools used by the MCP Server.

- :material-folder-open: **[Resources](resources/index.md)**  
  Explore the resource types available through the server.

- :material-message-text: **[Prompts](prompts/index.md)**  
  Use the built-in prompt templates for common workflows.

</div>