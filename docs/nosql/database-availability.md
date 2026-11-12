---
title: Database Availability
description: How the Actian MCP Server for NoSQL behaves when a database is busy, slow, or down, from the call cap and deadline to recovery without a restart, and what to do when a database cannot be used.
---

# Database Availability

How the MCP server behaves when a database is busy, slow, or down, and what to do then. It applies to the database without targets (`nsql.connectionURL`) and to the database of each target [with targets](targets/index.md). It covers the cap on calls in flight, the deadline for a call, idle connections, a database that is down at startup, recovery when it comes back, and what to do in each case.

## What Each Database Gets

Each database has its own connection pool to the NoSQL server, its own count of calls in flight, and a deadline for every call. With targets, that holds for each target's database separately. A slow or frozen database fills its own slots, not those of another database. The threads that run the calls are shared by every database.

## Properties

| Property | Default | Description |
|----------|---------|-------------|
| `nsql.db.max-calls` | `10` | Maximum number of concurrent calls per database, reads and writes together. A call beyond the cap is refused at once and never queued. `0` means no cap. A negative value stops the server at startup. |
| `nsql.db.call-deadline` | `30s` | Maximum duration of a read call, opening the database included. A write is covered only while it opens the database. `0` means no deadline. |
| `nsql.db.connect-timeout` | `10s` | Longest the network connect to the NoSQL server may take before the call fails as server unreachable. It covers the connect only, and the call deadline covers the protocol handshake after it. `0` leaves the NoSQL library's own default, which has no timeout. Must be shorter than the call deadline when both are set, so a call deadline of 10 seconds or less needs a shorter connect timeout. At most 2147483647 milliseconds. |
| `nsql.db.idle-timeout` | `10m` | Time without a call after which a database's connection pool is closed. The next call opens it again. `0` never closes an idle pool. |
| `nsql.db.connect-on-startup` | `true` | Without targets only: whether the database is opened at startup. See [Starting with a Database Down](#starting-with-a-database-down). |

Durations are written like the defaults, for example `30s` or `10m`. Except for `0`, a duration is at least one millisecond and at most 365 days. A value outside these rules stops the server at startup, and the failure lists every refused property by name.

At startup the server logs the limits in effect. It also logs a warning when `nsql.db.max-calls` times the number of databases is more than `quarkus.thread-pool.max-threads`, because calls to databases that do not answer could then occupy every worker thread. The server starts either way. No warning is logged when the two are equal, or when there is no cap.

## Call Cap and Deadline

Every tool call, resource read, and prompt request at a database takes one slot for as long as it runs and releases it however it ends. The same holds for the tools, resources, resource templates, and prompts of an [extension](extensions/index.md). With targets, plain `/mcp` serves no database and takes no slot.

The cap counts calls in flight per database. A call that finds every slot taken is refused at once with a message that the database is busy. It is not queued.

The deadline covers a read, which is a query, a cursor page, a fetch by LOID (Logical Object ID), a schema read, a resource, or a prompt, and it includes opening the database. A read that outlives the deadline is interrupted and answers that the database did not answer in time. A result that arrives after the deadline is not passed on. The database's connection pool is then closed, and the next call opens a new one.

A write is different:

- The deadline covers only opening the database. Once the database is open, the write runs to its end and is never interrupted, including the wait for the person's confirmation.
- A write on a stateful client keeps its slot while the person decides, up to `nsql.writes.confirmation-timeout-seconds`, so other calls to that database can find it full. A write on a stateless client holds nothing between its two calls.

Extensions follow the same split. An extension tool that is not read-only is treated as a write: the MCP server opens the database of the call before the tool's handler runs, and only that opening is under the deadline. While the database is down, such a tool therefore answers that the database is unavailable or did not answer in time, even if its handler never uses the database. Everything else an extension adds (read-only tools, resources, resource templates, and prompts) is treated as a read: the whole handler runs under the deadline and is interrupted if it takes longer.

The cap and the deadline bound the effect of a hung database and do not remove it. See [A Hung Database Is Bounded](limits.md#a-hung-database-is-bounded) for what they do not cover.

## Idle Close and Reopen

A database's connection pool is closed when no call has started or ended on it for `nsql.db.idle-timeout`. The server checks every `nsql.cursor.cleanup.interval`, which is `60s` by default, so a pool can close up to one interval after the timeout has passed. A pool with a call in flight or an open cursor stays open. The next call to a closed pool opens it again.

## Starting with a Database Down

What happens at startup depends on the mode:

- **With targets**, a database that is down never stops startup. Each target opens its database on first use, so the target exists, and its calls answer that it is unavailable until its NoSQL server is reachable. `nsql.db.connect-on-startup` has no effect.
- **Without targets**, `nsql.db.connect-on-startup` decides:
    - With `true`, which is the default, the server opens its database while it starts. A database that is down at that moment stops startup: start the NoSQL server, or set `nsql.db.connect-on-startup=false`.
    - With `false`, the server starts without connecting and opens the database on the first call. A database that is down or whose host does not resolve does not stop startup. A `nsql.connectionURL` that cannot be parsed still stops startup, because it is checked without connecting.

## Recovery without a Restart

Every call tries to reach the database again. A failed attempt leaves nothing behind, and calls that arrive during an attempt share its outcome, so a burst of calls against a database that is down is one attempt. A database that comes back is used again at the next call, with no restart of the MCP server.

A call that fails because the database cannot be used says why. The answer names the target, or says "the database" without targets, and never carries the host, the password, or a file path on the MCP server. The failure also closes the pool the call used, so the next call opens a new one. Each reason, and what to do about it, is listed under [When a Database Cannot Be Used](#when-a-database-cannot-be-used).

## When a Database Cannot Be Used

| Situation | Cause | What to do |
|-----------|-------|------------|
| The database is busy | It already has `nsql.db.max-calls` calls in flight. A write on a stateful client that waits for confirmation holds a slot too. | Try again later. If it recurs, look for calls that stay open before raising `nsql.db.max-calls`, and keep the shared worker threads in mind. |
| The database does not answer in time | A read, or the opening of the database for a write, took longer than `nsql.db.call-deadline`. The call was interrupted and the connection pool closed. | Check that the NoSQL server responds. The next call opens a new pool. Raise `nsql.db.call-deadline` only if calls that work need longer. |
| The NoSQL server cannot be reached | The network connect to the host and port of the connection URL failed, or did not finish within `nsql.db.connect-timeout`. | Check that the NoSQL server runs and that the MCP server can reach its host and port. No restart is needed. |
| The login is refused | The NoSQL server refused the user and password of the connection URL, with a NoSQL error code. | Correct the user and password. A login for a target kept in a directory is changed by replacing its file, see [Changing Targets Without a Restart](targets/without-restart.md). Any other connection URL is read at startup, so restart the server. The login also needs read-write access, see [The Login Needs Read-Write Access](limits.md#the-login-needs-read-write-access). |
| The database does not exist | The NoSQL server has no database with the name in the connection URL. The code is 7001. | Correct the database name, or create the database. |
| The database is not started, or the login lacks DBA privilege | The NoSQL server is up but the database is not started, or the login has no DBA privilege. After a NoSQL server restart, a login without it gets this answer until a DBA login starts the database. The code is 7245. | Have a DBA login start the database. Calls recover without a restart. |
| An open query stops paging after an outage | The outage closed the connection pool the query's cursor was open on. | Run the query again. |

## Next Steps

<div class="grid cards" markdown>

- :material-database: **[Targets](targets/index.md)**  
  Serve several databases through named targets from one MCP server.

- :material-pencil: **[Write Support](write-support.md)**  
  Turn on the write tools and see why they may be missing from a client.

- :material-alert-circle: **[Limits](limits.md)**  
  What the call limits protect against and what they do not.

</div>
