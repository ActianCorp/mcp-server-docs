---
title: What's New
description: New features and changes in Actian MCP Server 1.2.0, including multi-target deployments, resource-server mode, Ingres health tools, Analytics Engine vector search, and the VectorAI DB plugin, followed by the 1.1.0 changes.
---

# What's New in Actian MCP Server 1.2.0

The release of Actian MCP Server, version 1.2.0, offers the following new features and changes:

- [Multi-Target Deployments](#multi-target-deployments)
- [Resource-Server Mode](#resource-server-mode)
- [Ingres Health Tools](#ingres-health-tools)
- [Analytics Engine Vector Search](#analytics-engine-vector-search)
- [Actian VectorAI DB Support](#actian-vectorai-db-support)
- [Zen Updates](#zen-updates)
- [NoSQL Updates](#nosql-updates)
- [Tool Annotations and Tool Changes](#tool-annotations-and-tool-changes)

## Multi-Target Deployments

One container can now serve many databases instead of running one container per database. A `targets` block in `conf.json` lists the databases, each database gets its own URL, and OAuth scopes grant access to each database separately. Targets can also be added or removed without restarting the server, by using `targets.d` files. A deployment without a `targets` block works as before.

Multi-target deployments are available for Actian Ingres, Actian Analytics Engine, HCL Informix, and Actian Zen. Zen also supports read-only personas.

For more information, see [Ingres](../ingres/multi-target.md), [Analytics Engine](../analytics-engine/multi-target.md), [HCL Informix](../hcl-informix/multi-target.md), and [Zen](../zen/multi-target.md).

## Resource-Server Mode

An application that has already signed the user in can now call the MCP Server with an access token from the identity provider (IdP), without a second OAuth login. The server verifies each token against the IdP's published signing keys and runs the call as the user named in the token. The Auth0 and Keycloak guides describe the IdP setup, including the per-target scopes, and how a calling application obtains a token.

For more information, see [Ingres](../ingres/authentication/resource-server.md), [Analytics Engine](../analytics-engine/authentication/resource-server.md), and [Zen](../zen/authentication/index.md#resource-server-mode).

## Ingres Health Tools

Seven built-in, read-only tools report the operational health of the Ingres installation and the connected database. An AI assistant can use them to answer questions about checkpoints, locks, and optimizer statistics without catalog queries.

For more information, see [Health Tools](../ingres/health-tools.md).

## Analytics Engine Vector Search

The server now shows an AI agent which columns are `VECTOR` columns, and the `vector_search` tool returns the rows nearest to a query vector. `VECTOR` columns require Analytics Engine 8.0 or later.

For more information, see [Vector Search](../analytics-engine/vector-search.md).

## Actian VectorAI DB Support

A new Actian MCP Server for VectorAI DB provides semantic search over vector collections, with optional write support that requires approval for each write. It includes tools, prompts, and resources, OAuth with Auth0 or Keycloak, and custom extensions.

For more information, see [Actian VectorAI DB](../vectorai-db/index.md).

## Zen Updates

Zen gains multiple databases from one server, resource-server mode, a call log, a Deployment Scenarios page, the `list_accessible_targets` tool, and tool annotations for each mode.

For more information, see [Zen](../zen/index.md) and [Deployment Scenarios](../zen/deployment.md).

## NoSQL Updates

- The server accepts tokens only when the `aud` claim contains a value set in `quarkus.oidc.token.audience`, and the Keycloak guide describes token exchange for a calling application.
- A new page describes the stateful and stateless Model Context Protocol (MCP) versions, and how a write is confirmed on each.
- `get_objects_by_loids` reports the LOIDs it did not find in `notFoundLoids`.

For more information, see [Authentication](../nosql/authentication/index.md) and [Protocol Versions](../nosql/protocol-versions.md).

## Tool Annotations and Tool Changes

- Each tool declares MCP tool annotations, which clients can use to decide whether to run a tool without asking first.
- For Ingres, `list_indexes` lists the indexes on a table.
- For Ingres, `list_tables` shows each table's owner, and `describe_table` accepts an owner-qualified name.
- A multi-target error now includes the reason.

For more information, see [Ingres Tools](../ingres/tools/index.md#tool-annotations).

# What's New in Actian MCP Server 1.1.0

The release of Actian MCP Server, version 1.1.0, offers the following new features and changes:

- [Unified Query Modes](#unified-query-modes)
- [HITL Write Approval Path](#hitl-write-approval-path)
- [Warehouse Sidecar Support](#warehouse-sidecar-support)
- [Custom Extension Support](#custom-extension-support)

  
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

In the SaaS deployment, the MCP Server deploys as a sidecar alongside the warehouse leader pod on the Actian Analytics AI Platform. Clients connect using only the MCP server URL, and no separate Auth0 setup is required. Internally, the server acts as an OAuth2 Authorization Server proxy and hides the Auth0 token exchange from the clients entirely.

For more information, see [Actian MCP Server for Analytics Engine (SaaS)](../analytics-engine/saas.md).

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
