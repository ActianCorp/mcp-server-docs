---
title: Write Support
description: Enable data-modifying SQL on the Actian MCP Server with query_mode, and understand the scope check and human approval that authorize every write.
---

# Write Support

By default, the Actian MCP Server permits only read queries. On the SQL databases, set `query_mode` to `read-write` in `conf.json` to also allow Data Manipulation Language (DML) statements, that is `INSERT`, `UPDATE`, and `DELETE`.

Write support remains off until it is enabled. Existing read-only deployments are not affected.

!!! note "Actian NoSQL works differently"
    It has no DML statements: writes go through dedicated object tools, governed by their own setting. See [Write support for Actian NoSQL](../nosql/write-support.md).

Extensions can write too, through the same authorization checks described below. See [Extensions](../extensions/index.md).

Which tools accept a write, and how, depends on the database. See the Tools page for the relevant database, for example [Ingres tools](../ingres/tools/index.md) or [Analytics Engine tools](../analytics-engine/tools/index.md). The `query_mode` setting and the authorization checks described below apply the same way regardless of which tool performs the write.

!!! note "Zen routes writes to a separate tool, and changes its tool list"
    On Ingres and Analytics Engine, `execute_query` performs the write once `query_mode` is
    `read-write`. On [Zen](../zen/tools/index.md) it never does: writes go to `execute_write_query`
    and to `orm_operation`, and enabling write mode also removes `blob_operation` and
    `database_manage` from the registered tools. Zen additionally counts the rows a conditional
    `UPDATE`/`DELETE` matches and shows that number in the approval prompt.

## Enabling Write Mode

Set `query_mode` in the `conf.json` file:

| Value | Behavior |
|-------|----------|
| `read-only` | Default. Only read queries are permitted. |
| `read-write` | Read queries plus `INSERT`, `UPDATE`, and `DELETE` are permitted. |

```json
{
  "query_mode": "read-write"
}
```

!!! note "Data Definition Language is always blocked"
    Enabling write mode does not permit Data Definition Language (DDL) or administrative statements. `CREATE`, `ALTER`, `DROP`, and `GRANT` are rejected, and so are `SET`, `ENABLE`, `DISABLE`, and `SELECT ... INTO`. This is not configurable. Use the database's native tools for schema changes.

## Authorizing a Write

In `read-write` mode, every DML statement must pass two independent checks before it reaches the database. Either one can reject it.

| Check | What it requires | When it applies |
|-------|------------------|-----------------|
| `mcp:write` scope | The access token must carry the `mcp:write` scope. | Only when OAuth is enabled. A read-only server never requests or requires this scope. |
| Human approval | A person must approve the statement in the connected client. | Always, unless disabled with `write_confirmation`. |

The scope is checked first, so a caller without it is rejected before anyone is asked to approve anything.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {'fontSize': '18px', 'fontFamily': 'arial'}}}%%
sequenceDiagram
    participant User as User
    participant Client as MCP Client
    participant Server as MCP Server
    participant DB as Database

    Client->>Server: Write request (INSERT / UPDATE / DELETE)
    Server->>Server: Check mcp:write scope
    alt Scope missing
        Server-->>Client: Rejected (authorization error)
    else Scope present
        Server->>Client: Request approval
        Client->>User: Show statement, table, and database
        alt User approves
            User-->>Client: Approve
            Client-->>Server: Approved
            Server->>DB: Run statement
            DB-->>Server: Rows affected
            Server-->>Client: Success
        else Declined, no response, or client cannot prompt
            Client-->>Server: Not approved
            Server-->>Client: Rejected (write not approved)
        end
    end
```

The approval prompt uses the Model Context Protocol (MCP) elicitation capability, which not every client implements. If the connected client cannot display the prompt, the write is rejected, exactly as if a person had declined it. See [Connecting MCP Clients](../mcp-clients/index.md#elicitation-support-for-write-approval) for which clients support it.

To configure the `mcp:write` scope in the identity provider, see [Auth0](../authentication/auth0/index.md) or [Keycloak](../authentication/keycloak/index.md).

## Skipping the Approval Prompt

Some clients cannot display the approval prompt. For those deployments, set `write_confirmation` to `false` in `conf.json` to run the server's built-in write tools without asking for approval:

```json
{
  "query_mode": "read-write",
  "write_confirmation": false
}
```

!!! warning "This removes human oversight of every write"
    With `write_confirmation` set to `false`, the server runs `INSERT`, `UPDATE`, and `DELETE` statements as soon as they are requested. Nobody is asked first. Use it only when the client cannot prompt and unattended writes by the AI agent are acceptable.

    The `mcp:write` scope check still applies. Disabling the prompt does not grant write access to callers that lack the scope.

    This setting covers the built-in write tools only. An extension that asks for approval itself always prompts, whatever this is set to. See [Extensions](../extensions/index.md#extension-security-controls).

The server records what it skipped. At startup it logs a warning banner stating that write confirmation is disabled, and it logs a warning for each write that ran without approval. Those entries name the tool only. They never include the statement text or the row values.

## Next Steps

<div class="grid cards" markdown>

- :material-database-cog: **[Ingres configuration](../ingres/index.md#configuration-reference)**  
  The `query_mode` and `write_confirmation` fields for Actian Ingres.

- :material-chart-box: **[Analytics Engine configuration](../analytics-engine/index.md#configuration-reference)**  
  The same fields for Actian Analytics Engine.

- :material-database: **[Zen configuration](../zen/index.md#configuration-reference)**  
  The same fields for Actian Zen, which registers a different tool set per mode.

- :material-shield-check: **[Authentication](../authentication/index.md)**  
  Set up the `mcp:write` scope in Auth0 or Keycloak.

- :material-connection: **[MCP clients](../mcp-clients/index.md#elicitation-support-for-write-approval)**  
  Which clients can display the write approval prompt.

</div>
