---
title: What's New
description: New features and changes in Actian MCP Server 1.1.0, including unified query modes, human-in-the-loop write approval, warehouse sidecar deployment, and custom extensions.
---

# What's New in Actian MCP Server 1.1.0

The release of Actian MCP Server, version 1.1.0, offers the following new features and changes:

- [What's New in Actian MCP Server 1.1.0](#whats-new-in-actian-mcp-server-110)
  - [Unified Query Modes](#unified-query-modes)
  - [HITL Write Approval Path](#hitl-write-approval-path)
  - [Warehouse Sidecar Support](#warehouse-sidecar-support)
  - [Custom Extension Support](#custom-extension-support)
  - [Next Steps](#next-steps)

## Unified Query Modes

The `conf.json` file supports exactly two query modes: `read-only`, which is the default, and `read-write`. In `read-only` mode, the server permits only read queries. In `read-write` mode, it also permits the Data Manipulation Language (DML) statements `INSERT`, `UPDATE`, and `DELETE`.

Data Definition Language (DDL) operations are unsupported in both modes. The server rejects statements such as `CREATE`, `ALTER`, `DROP`, and `GRANT`, and this behavior is not configurable. Use the native database tools for schema changes.

For more information, see [Enabling Write Mode](../ingres/write-support.md#enabling-write-mode).

## HITL Write Approval Path

Every write passes through a human-in-the-loop (HITL) approval path. Writes require `"query_mode": "read-write"` in `conf.json`; in that mode, a DML statement must satisfy two independent checks before it reaches the database:

- The access token carries the `mcp:write` OAuth scope, when OAuth is enabled.
- A person explicitly approves the statement in the connected MCP client.

The server evaluates the scope first, so a caller without it is rejected before an approval is requested.

For more information, see [Authorizing a Write](../ingres/write-support.md#authorizing-a-write).

## Warehouse Sidecar Support

The MCP Server deploys as a sidecar alongside the warehouse leader pod. Clients connect using only the MCP server URL, and no separate Auth0 setup is required. Internally, the server acts as an OAuth2 Authorization Server proxy and hides the Auth0 token exchange from the clients entirely.

For more information, see [Actian MCP Server on a Managed Warehouse](../analytics-engine/managed-warehouse.md).

## Custom Extension Support

Plain Python modules mounted at `/app/extensions` add custom tools and resources dynamically, without any modification to the core database plugins. Extensions run behind the same authentication and write controls as the built-in tools.

For more information, see [Extensions](../ingres/extensions/index.md).

## Next Steps

<div class="grid cards" markdown>

- :material-book-open-variant: **[Introduction](../intro/index.md)**  
  To review the core concepts and the architecture of the server, see [Introduction](../intro/index.md).

- :material-rocket-launch: **[Get Started](../get-started/index.md)**  
  To deploy an Actian MCP Server instance and connect it to an AI client, see [Getting Started with MCP Server](../get-started/index.md).
</div>
