---
title: What's New
description: New features and changes in Actian MCP Server 1.2.0, including multi-target deployments, resource-server mode, Ingres health tools, Analytics Engine vector search, and the VectorAI DB plugin.
---

# What's New in Actian MCP Server 1.2.0

Actian MCP Server 1.2.0 adds the following features and changes:

- [Multi-Target Deployments](#multi-target-deployments)
- [Resource-Server Mode](#resource-server-mode)
- [Ingres Health Tools](#ingres-health-tools)
- [Analytics Engine Vector Search](#analytics-engine-vector-search)
- [Actian VectorAI DB Support](#actian-vectorai-db-support)
- [Zen Updates](#zen-updates)
- [NoSQL Updates](#nosql-updates)
- [Tool Annotations and Tool Changes](#tool-annotations-and-tool-changes)

## Multi-Target Deployments

One container can now serve many databases instead of running one container for each database. You list the databases in a `targets` block in `conf.json`. Each database gets its own URL, and OAuth scopes control access to each database separately. You can add or remove targets without restarting the server by using `targets.d` files. A deployment without a `targets` block works as before.

Multi-target deployments work with Actian Ingres, Actian Analytics Engine, HCL Informix, and Actian Zen. Zen also supports read-only personas.

For more information, see [Ingres](../ingres/multi-target.md), [Analytics Engine](../analytics-engine/multi-target.md), [HCL Informix](../hcl-informix/multi-target.md), and [Zen](../zen/multi-target.md).

## Resource-Server Mode

An application that has already signed the user in can now call the MCP Server with an access token from the identity provider (IdP). The user does not need a second OAuth login. The server checks each token against the IdP's published signing keys and runs the call as the user named in the token. The Auth0 and Keycloak guides describe the IdP setup, including the scopes for each target, and how a calling application gets a token.

For more information, see [Ingres](../ingres/authentication/resource-server.md), [Analytics Engine](../analytics-engine/authentication/resource-server.md), and [Zen](../zen/authentication/index.md#resource-server-mode).

## Ingres Health Tools

Seven built-in, read-only tools report the health of the Ingres installation and the connected database. An AI assistant can use them to answer questions about checkpoints, locks, and optimizer statistics without catalog queries.

For more information, see [Health Tools](../ingres/health-tools.md).

## Analytics Engine Vector Search

The server now shows an AI agent which columns are `VECTOR` columns. The `vector_search` tool returns the rows nearest to a query vector. `VECTOR` columns require Analytics Engine 8.0 or later.

For more information, see [Vector Search](../analytics-engine/vector-search.md).

## Actian VectorAI DB Support

A new Actian MCP Server for VectorAI DB provides semantic search over vector collections. Writes are optional, and each write needs approval. The server includes tools, prompts, and resources. It supports OAuth with Auth0 or Keycloak, and custom extensions.

For more information, see [Actian VectorAI DB](../vectorai-db/index.md).

## Zen Updates

Zen now supports several databases from one server and resource-server mode. It also adds a call log, the `list_accessible_targets` tool, tool annotations for each mode, and a Deployment Scenarios page.

For more information, see [Zen](../zen/index.md) and [Deployment Scenarios](../zen/deployment.md).

## NoSQL Updates

- The server accepts a token only when its `aud` claim contains a value set in `quarkus.oidc.token.audience`. The Keycloak guide also describes token exchange for a calling application.
- A new page describes the stateful and stateless versions of the Model Context Protocol (MCP) and how the server confirms a write on each.
- `get_objects_by_loids` lists the LOIDs it did not find in `notFoundLoids`.

For more information, see [Authentication](../nosql/authentication/index.md) and [Protocol Versions](../nosql/protocol-versions.md).

## Tool Annotations and Tool Changes

- Each tool declares MCP tool annotations. Clients can use them to decide whether to run a tool without asking first.
- For Ingres, `list_indexes` lists the indexes on a table.
- For Ingres, `list_tables` shows each table's owner, and `describe_table` accepts an owner-qualified name.
- A multi-target error now includes the reason.

For more information, see [Ingres Tools](../ingres/tools/index.md#tool-annotations).

## Next Steps

<div class="grid cards" markdown>

- :material-book-open-variant: **[Introduction](../intro/index.md)**  
  To review the core concepts and the architecture of the server, see [Introduction](../intro/index.md).

- :material-rocket-launch: **[Get Started](../get-started/index.md)**  
  To deploy an Actian MCP Server instance and connect it to an AI client, see [Getting Started with MCP Server](../get-started/index.md).
</div>
