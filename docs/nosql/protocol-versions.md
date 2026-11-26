---
title: Protocol Versions
description: Which Model Context Protocol versions the Actian MCP Server for NoSQL accepts, how a write is confirmed on each, and what extension authors need to know.
---

# Protocol Versions

The Actian MCP Server for NoSQL supports two families of the Model Context Protocol (MCP) on the same endpoint. Most client actions are identical on both. This page covers what differs: how a write is confirmed, plus a few details in the server log and in one error code.

## Accepted Protocol Versions

| Family | Versions | How a client starts |
|--------|----------|---------------------|
| Stateful | 2024-11-05 through 2025-11-25 | An `initialize` handshake, after which the server keeps a session for that client. |
| Stateless | 2026-07-28 | A `server/discover` request. There is no session: every request is self-contained and carries its protocol version and capabilities in `_meta`. |

Both arrive on the same endpoint, `/mcp`, or `/mcp/{target}` with targets, and the client chooses per request. No setting refuses stateless clients, and no setting is needed to accept them.

Which protocol a client uses is decided by the client. To make a client use the stateful protocol, see that client's own documentation.

## Write Confirmation on Each Protocol

Every write still needs a person's confirmation, and the server still enforces the answer. What differs is how the question travels. See [Write Support](write-support.md) for the other checks a write must clear.

| Protocol | How the confirmation works |
|----------|----------------------------|
| Stateful | The server sends the confirmation prompt while the tool call waits. The call stays open until the person answers or the timeout closes it. |
| Stateless | The first call returns the confirmation question and writes nothing. The client shows it, then repeats the same call with the answer. Only then does the write run. The first call does not stay open. |

For a stateless client, the approval the server records when it asks has these properties:

- It is valid only for that exact call: the same tool, the same arguments, and, when authentication is on, the same signed-in user.
- With targets, it is also valid only for the target it was asked at, and for the database that target pointed at then. A retry at another target is refused. So is a retry after the target was removed or began to point at another host, port, or database. A change of the user or password of the target keeps the approval.
- It can be used once.
- It stays valid for the time set in `nsql.writes.confirmation-timeout-seconds` (default `60`). This is how long the person has to answer. The server refuses a later answer, and the client must run the operation again.
- The server refuses a retry that changes an argument or uses an expired, unknown, or already used approval, and it writes nothing. The client must run the operation again from the start, which asks the question again. The server also does not accept a "yes" sent without an approval. It asks the question instead of writing.
- Declining or cancelling gets the same refusal messages as on the stateful protocol, each of which names the reason.
- A client that declares only URL-mode elicitation cannot show the confirmation form, so it never sees the write tools, on either protocol. For a stateless client, the server decides this on every request, from the capabilities that the request declares.

## Running More Than One Server Instance

!!! warning "Route each client to one instance"
    A stateless approval is held in the memory of the instance that asked, the same way query cursors are. If the retry reaches a different instance, that instance does not know the approval and refuses the retry. Nothing is written, so the failure is safe, but the client cannot complete the operation. Route each client's requests to one instance (sticky routing).

With targets that come from a directory, each instance also reads its own copy of that directory. See [Several Instances and Directory Changes](limits.md#several-instances-and-directory-changes).

## Resource Not Found

Reading `db://schema/class/{className}`, or `db://schema/{target}/class/{className}` with targets, for a class that does not exist returns JSON-RPC error `-32602` (invalid params) to a stateless client and `-32002` (resource not found) to a stateful client. The 2026-07-28 specification changed the code. The server uses the code for the protocol that the client uses.

## Server Log

For each stateless `server/discover`, the server writes one `INFO` line that names the client, the protocol version, whether the client supports elicitation, and whether writes are enabled on the server (`nsql.writes.enabled`). The server logs nothing of its own for the calls that follow. A stateful client still produces a line of the same kind once per handshake. Each stateless client decides how often to send `server/discover` again.

## For Extension Authors

An extension write tool that calls `context.confirm(...)` works on both protocols without changes. On the stateless protocol, the handler runs again from the start after the person approves. So keep side effects after `confirm()`, do not catch exceptions around it, and call it at most once for each tool call. The server refuses a second call in one stateless call. For details, see [Write Gating for Extension Tools](extensions/index.md#write-gating-for-extension-tools).
