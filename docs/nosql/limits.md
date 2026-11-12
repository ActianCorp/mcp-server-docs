---
title: Limits
description: What the call limits of the Actian MCP Server for NoSQL do and do not protect against, and the other limits of the server, with targets and without.
---

# Limits

This page lists the limits of the Actian MCP Server for NoSQL in one place. They hold with targets and without, except those under [With Targets](#with-targets).

## A Hung Database Is Bounded

Calls run on a thread pool that all databases share. Its size is the Quarkus default of the greater of 8 times the number of processor cores and 200 threads, unless you set `quarkus.thread-pool.max-threads`. A frozen database holds at most `nsql.db.max-calls` of those threads, each for at most `nsql.db.call-deadline` when the call is a read, and a host that cannot be reached fails at `nsql.db.connect-timeout`. See [Call Cap and Deadline](database-availability.md#call-cap-and-deadline). This bounds the effect of a hung database and does not remove it. The limits do not cover the following:

- Callers of a frozen database still wait up to the deadline, and a call beyond the cap is refused, not queued.
- A write that has started is not interrupted. The deadline covers only the opening of its database.
- With `nsql.db.call-deadline=0` there is no deadline, so a NoSQL server that accepts the connection and then freezes can hold a call without end.
- With `nsql.db.max-calls=0` there is no cap, so calls to a frozen database can occupy every thread.
- When `nsql.db.max-calls` times the number of databases is more than the thread pool, which the server reports at startup, enough frozen databases together can still occupy every thread.
- There is no fairness between callers. One caller can fill the cap of a database.
- The cleanup of expired cursors runs outside these limits, and an idle pool can close up to one `nsql.cursor.cleanup.interval` late.

## Scopes Are the Only Authorization

Each database is opened with the one NoSQL login written in its connection URL: `nsql.connectionURL` without targets, and the target's connection URL with targets. Every caller that the [scopes](authentication/index.md) admit reads there, and writes if granted, as that login. There is no per-caller database identity and no separate login for reads and writes.

## The Login Needs Read-Write Access

The NoSQL server refuses a read-only login with NoSQL error 3036, even when writes are turned off. Callers then get the answer that the login is refused, see [When a Database Cannot Be Used](database-availability.md#when-a-database-cannot-be-used).

## Open Cursors Can Starve a Database

An open `execute_query` cursor holds a pooled connection until it is drained or expires. A cursor expires after `nsql.cursor.ttl` without use, `300s` by default, and the cleanup that removes it runs every `nsql.cursor.cleanup.interval`. The pool holds 10 connections, so about 10 undrained cursors can make other calls to that database fail until some of them expire.

## Distributed Databases

The distributed form `database1@host1|database2@host2` is not supported, in `nsql.connectionURL` or in a target's connection URL. A URL that contains `|` is refused: at startup the server does not start, and at a reload the running set stays as it was. For the same reason, a password cannot contain `|`.

## Revocation and Process State

- Revoking a grant at the identity provider takes effect when the access token expires, so keep access tokens short-lived.
- Cursors, pending write confirmations of stateless clients, rate-limit buckets, and session pins live in the memory of one server process. With several instances of the MCP server behind one address, for example the replicas of a Kubernetes Deployment, route a client's requests to one instance (sticky routing). A request that reaches another instance does not find them, and a stateless confirmation answered at another instance is refused, so the client starts over.

## LOIDs Belong to One Endpoint

A LOID (Logical Object ID) is valid only at the endpoint that returned it. Database IDs repeat across NoSQL servers, so a LOID sent to another endpoint, of another target or another MCP server, can name an unrelated object there, and the MCP server cannot detect this. `update_objects` needs an `expectedVersion` read at the same endpoint.

## With Targets

### One Audience for Every Target

One audience, `quarkus.oidc.token.audience`, covers every target. The scopes decide which target a token reaches.

### Several Instances and Directory Changes

Each instance reads its own copy of `nsql.targets.dir` on its own schedule, so for a short time one instance can serve a target that another does not. A client that reaches a different instance can see a target that exists at one instance and not at the other.

### Directory Targets

- Removing a target does not stop the calls already running on it, writes included. They run to the end, and only new requests are refused, from the reload that applies the removal.
- One bad file holds back every pending change until it is fixed.
- The directory holds credentials in clear text. See [Credentials in the Directory](targets/without-restart.md#credentials-in-the-directory).

### Subscriptions Reveal Which URIs Exist

A stateful client can learn whether a schema resource or an extension resource exists at another target by subscribing to its address (its URI). The server answers a subscription to an address that exists with an empty success, and to one that never existed with an error that the resource was not found. No schema content is exposed, but a caller can tell whether a target name exists, which the `403` reply for a target without a scope is built to prevent.

## Next Steps

<div class="grid cards" markdown>

- :material-database: **[Targets](targets/index.md)**  
  Targets, names, connection URLs, and what an agent sees.

- :material-connection: **[Database Availability](database-availability.md)**  
  The call cap, the call deadline, idle connections, and what to do when a database cannot be used.

</div>
