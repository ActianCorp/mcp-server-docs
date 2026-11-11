---
title: Targets
description: How one Actian MCP Server for NoSQL serves databases through named targets, how a target is configured and reached, and what an agent sees.
---

# Targets

One Actian MCP Server for NoSQL can serve several NoSQL databases through named targets, and a client reaches each target at `/mcp/{target}`.

## What a Target Is

A target is a name and a connection URL:

| Part | Meaning |
|------|---------|
| Name | The path segment clients use, so the target `sales` is served at `/mcp/sales`. |
| Connection URL | The NoSQL database the target serves, in the form `database@host[:port][#user[:password]]`. See [Target Names and Connection URLs](#target-names-and-connection-urls). |

The host, port, and database name stay in the MCP server's configuration. A client learns only the target name, and the MCP server's own texts about a target name the target, never its host.

## Choosing a Mode

The properties you set select the mode.

| You set | Mode |
|---------|------|
| `nsql.connectionURL` | Without targets. The server serves the database that the URL names, at `/mcp`, and every tool is available there. |
| `nsql.targets[i].name` with `nsql.targets[i].connectionURL`, or `nsql.targets.dir`, or both | With targets. Each target is served at `/mcp/{target}`, and plain `/mcp` only lists the targets. |

Setting `nsql.connectionURL` together with either of the others stops the server at startup, and so does setting none of the three. One target is enough for the server to run with targets: a single `nsql.targets` entry is served at `/mcp/{target}` like any other.

Across the documentation, "without targets" means that `nsql.connectionURL` is set, and "with targets" means that targets are configured, however many.

The `nsql.targets[i]` entries are read once at startup, so changing one needs a restart. Targets that come from a directory can be added, changed, and removed while the server runs. See [Changing Targets Without a Restart](without-restart.md).

## A Minimal Example

Two targets, `sales` and `hr`, written as indexed pairs of a name and a connection URL:

```properties
nsql.targets[0].name=sales
nsql.targets[0].connectionURL=sales_db@sales-db.example.com:5019#<USER>:${SALES_DB_PASSWORD}
nsql.targets[1].name=hr
nsql.targets[1].connectionURL=hr_db@hr-db.example.com#<USER>:${HR_DB_PASSWORD}
```

The `${...}` references are resolved when the server starts, so a password stays out of the file. A reference that resolves to nothing stops startup.

The indexed form is the only form. A list written without indexes, such as `nsql.targets=sales,hr`, stops startup. The same two targets as environment variables of the server process, with two underscores before the field name:

```shell
NSQL_TARGETS_0__NAME=sales
NSQL_TARGETS_0__CONNECTIONURL='sales_db@sales-db.example.com:5019#<USER>:<PASSWORD>'
NSQL_TARGETS_1__NAME=hr
NSQL_TARGETS_1__CONNECTIONURL='hr_db@hr-db.example.com#<USER>:<PASSWORD>'
```

The spelling with one underscore before the field is not read and stops startup.

## Target Names and Connection URLs

A target name:

- Is required, with 1 to 31 letters, digits, `_`, or `-`.
- Is matched exactly as written, case included, so `Sales` is not `sales`.
- Must be unique.
- Cannot be `sse`, which is reserved for the legacy server-sent events path `/mcp/sse`. A name such as `sse2` is an ordinary target name.

A connection URL has the form `database@host[:port][#user[:password]]`:

- The database name follows the same rule as a target name.
- The host is required. It holds letters, digits, `.`, `_`, and `-`, and starts and ends with a letter or digit.
- The port is optional and defaults to `5019`. It is 1 to 65535 without leading zeros.
- The user holds letters, digits, `_`, `-`, and spaces, and does not start or end with a space.
- The password needs a user. It holds printable characters, does not contain `|`, and does not start or end with a space. Without a user, the MCP server connects as the operating system user of the MCP server process.

Each target's database is opened with the login written in the target's URL. There is no server-wide login, so when several targets use the same login, write it in each of their URLs. For what the login needs and what it means for callers, see [Limits](../limits.md).

The server refuses two targets that name the same host, port, and database, with the port defaulting to `5019`, so `db@host` and `db@host:5019` count as the same database. It also refuses the distributed form `database@host|database@host`. See [Distributed Databases](../limits.md#distributed-databases).

## What an Agent Sees

Plain `/mcp` offers only the `list_accessible_targets` tool. It offers no other tool, no resource, no resource template, and no prompt. The tool answers from the configuration and the caller's token without contacting any database:

```json
{
  "targets": [
    {"name": "sales", "path": "/mcp/sales", "access": "write"},
    {"name": "hr", "path": "/mcp/hr", "access": "read"}
  ]
}
```

- `access` is `write` when `nsql.writes.enabled` is `true` and, with authentication on, the caller holds that target's write scope. Otherwise it is `read`.
- The entries follow the order of the configuration: the `nsql.targets[i]` targets by index, then the directory targets by name.
- With authentication on, the list holds only the targets the caller's token grants. With authentication off, every target is listed.
- A token grants a target through the scopes `actian:{target}:read` and `actian:{target}:write`. See [Scopes per Target](../authentication/scopes.md#scopes-per-target).

At `/mcp/{target}` the agent gets the usual tools, that target's schema resources under `db://schema/{target}/...` (see [Resources](../resources/index.md)), and the prompts (see [Prompts](../prompts/index.md)).

An extension is offered at every target unless its `nsql.extensions.jars.<id>.targets` property limits it to some of them. The limit decides where an extension is offered, and nothing more. See [Limiting an Extension to Some Targets](../extensions/index.md#limiting-an-extension-to-some-targets).

!!! note "A LOID belongs to one endpoint"
    A LOID (Logical Object ID) is valid only at the endpoint that returned it. Database IDs repeat across NoSQL servers, so the same LOID sent to another target can name an unrelated object there, and the MCP server does not detect this. `update_objects` needs an `expectedVersion` read at the same target, and `delete_objects` shows each object's class in its confirmation unless confirmation is turned off.

Other behaviour of the endpoints:

- A stateful session stays on the target it started on. Presenting its session id at another target's path answers `404`. A stateless client has no session, so this does not apply to it.
- The legacy server-sent events endpoint `/mcp/sse` is not available when targets are configured, and it answers `404`.
- A path that is not exactly `/mcp/{target}` with a valid target name answers `404`. With authentication off, so does a target name that is not configured. With authentication on, a target name that is not configured gets the same `403` as a target the caller may not read; see [What a Caller Gets](../authentication/scopes.md#what-a-caller-gets).

## Connecting on First Use

Each target opens its database on first use. At startup, the log lists each target with its database and server.

A target whose NoSQL server is down at startup still exists. Its calls answer that the target is unavailable, and every call tries the connection again, so the target works as soon as the NoSQL server is reachable.

The limits on calls, the call deadline, and how an idle connection is closed and reopened are set once for the MCP server and apply to each target's database separately. See [Database Availability](../database-availability.md).

## Log Lines

A console line written while a call is served at a target starts its message with the target name. Two settings do this, and both are set by default:

```properties
quarkus.log.console.filter=target-log
quarkus.log.console.format=%d{yyyy-MM-dd HH:mm:ss,SSS} %-5p [%c] (%t) %X{target}%s%e%n
```

To keep the name:

- If you change `quarkus.log.console.format`, keep `%X{target}` before the message.
- A filter applies only to the handler it is attached to, so no other handler carries the name by default. To tag another handler, attach the filter and add `%X{target}` before the message in that handler's format, for example `quarkus.log.file.filter=target-log`. The same holds for the syslog and socket handlers.

Lines with no request behind them (startup, shutdown, and scheduled jobs), lines at plain `/mcp`, and the line written when a stateless client first connects carry no name. Without targets no line carries one.

For the log levels and categories, see [Logging](../index.md#logging).

## Next Steps

<div class="grid cards" markdown>

- :material-database: **[Changing Targets Without a Restart](without-restart.md)**  
  Add, change, and remove a target without a restart.

- :material-alert-circle: **[Limits](../limits.md)**  
  What the call limits protect against and what they do not.

- :material-lock: **[Authentication](../authentication/index.md)**  
  Secure the server with OAuth 2.0 and an external identity provider.

- :material-key: **[Scopes](../authentication/scopes.md)**  
  The scopes that grant access to each target, and what a caller gets when one is missing.

- :material-tools: **[Tools](../tools/index.md)**  
  Explore the available MCP tools for NoSQL database operations.

- :material-folder-open: **[Resources](../resources/index.md)**  
  Learn more about schema metadata resources.

</div>
