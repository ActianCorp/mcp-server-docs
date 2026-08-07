---
title: Actian Data Platform
description: Connect MCP clients to an Analytics Engine warehouse in Actian Data Platform, where the MCP Server is managed and auto-configured.
---

# Actian MCP Server on Actian Data Platform

When your Analytics Engine runs as a warehouse in Actian Data Platform, the MCP Server is configured for you. There is nothing to install, no container to run, and no `conf.json` to write. You only need the warehouse endpoint and an MCP client.

To run the server yourself against your own Analytics Engine instance, see [Actian Analytics Engine](index.md) instead.


## Connect Your MCP Client

The MCP endpoint for a warehouse is:

```
https://<warehouse-host>/mcp
```

Use the same warehouse host shown on the warehouse **Connections** page. For example, in Visual Studio Code:

```json
{
  "servers": {
    "actian-warehouse": {
      "type": "http",
      "url": "https://<warehouse-host>/mcp"
    }
  }
}
```

For Claude Desktop, GitHub Copilot, and Python client formats, see [Connecting MCP Clients](../mcp-clients/index.md).

!!! note "Before you connect"
    The endpoint is available only on warehouses that have MCP enabled, and only while the warehouse is running. Data Platform also restricts warehouse access by IP address, and this applies to MCP connections. Make sure the machine running your MCP client falls within the warehouse IP allow list. For more information, see [Data Access and Authentication](https://docs.actian.com/actiandataplatform/Security/Data_Access_and_Authentication.htm) in the Actian Data Platform documentation.


## Authentication

The MCP client signs you in with an OAuth login against the warehouse. This is different from the other connection options on the **Connections** page, which use a database username and password.

After you sign in, queries run under your own database identity. The privileges that apply are the ones already granted to you on the warehouse, enforced per table. To grant or change those privileges, see [User Management](https://docs.actian.com/actiandataplatform/Connectivity/User_Management.htm) in the Actian Data Platform documentation.


## Write Operations

Write queries are enabled on Data Platform warehouses. Two conditions must be met before a write runs:

1. **Your database privileges allow it.** The warehouse enforces your existing grants on each table, so the MCP Server cannot write anything you could not write yourself.
2. **You approve the write.** The server describes the statement and waits for your confirmation before running it.

!!! warning "A client that cannot prompt cannot write"
    The approval request uses the Model Context Protocol (MCP) elicitation capability, which not every client implements. If your client does not support it, the server rejects the write exactly as if you had declined it. There is no silent approval, and the approval step cannot be turned off on Data Platform. Reads are unaffected.

    Claude Desktop and GitHub Copilot cannot display the prompt today. For the current list, see [Elicitation support for write approval](../mcp-clients/index.md#elicitation-support-for-write-approval).


## What Actian Manages

The following are configured and maintained by Actian, and cannot be changed for a warehouse:

- Transport security (TLS) and the server endpoint
- Database connection settings, including the connection pool
- Query mode, row limits, and log verbosity
- The OAuth provider used for sign-in

Custom extensions are not supported on Actian Data Platform. To load your own Python extensions, run the server yourself using the [Analytics Engine](index.md) configuration.


## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](tools/index.md)**  
  Learn more about the Analytics Engine tools used by the MCP Server.

- :material-folder-open: **[Resources](resources/index.md)**  
  Explore the resource types available through the server.

- :material-message-text: **[Prompts](prompts/index.md)**  
  Use the built-in prompt templates for common workflows.

</div>
