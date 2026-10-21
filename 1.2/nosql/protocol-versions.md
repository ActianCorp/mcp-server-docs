---
title: Protocol Versions
description: Which Model Context Protocol versions the Actian MCP Server for NoSQL accepts, how a write is confirmed on each, and what extension authors need to know.
---

# Protocol Versions

The Actian MCP Server for NoSQL speaks two families of the Model Context Protocol (MCP) on the same endpoint. Most of what a client does is identical on both. Two things differ, and this page covers them: how a write is confirmed, and a few details in the server log and in one error code.

## Accepted Protocol Versions

| Family | Versions | How a client starts |
|--------|----------|---------------------|
| Stateful | 2024-11-05 through 2025-11-25 | An `initialize` handshake, after which the server keeps a session for that client. |
| Stateless | 2026-07-28 | A `server/discover` request. There is no session: every request is self-contained and carries its protocol version and capabilities in `_meta`. |

Both arrive on the same `/mcp` endpoint, and the client chooses per request. No setting refuses stateless clients, and no setting is needed to accept them.

Which protocol a client uses is decided by the client. To make a client use the stateful protocol, see that client's own documentation.

## Write Confirmation on Each Protocol

Every write still needs a person's confirmation, and the server still enforces the answer. What differs is how the question travels. See [Write Support](write-support.md) for the other checks a write must clear.

| Protocol | How the confirmation works |
|----------|----------------------------|
| Stateful | The server sends the confirmation prompt while the tool call waits. The call stays open until the person answers or the timeout closes it. |
| Stateless | The first call returns the confirmation question and writes nothing. The client shows it, then repeats the same call with the answer. Only then does the write run. The first call does not stay open. |

For a stateless client, the approval the server records when it asks has these properties:

- It is valid only for that exact call: the same tool, the same arguments, and, when authentication is on, the same signed-in user.
- It can be used once.
- It lasts `nsql.writes.confirmation-timeout-seconds` (default `60`). For a stateless client this is how long the person has to answer; a later answer is refused and the operation must be run again.
- A retry with a changed argument, or with an expired, unknown, or already used approval, is refused and nothing is written. The client must run the operation again from the start, which asks the question afresh. A "yes" sent without an approval is not accepted either: the server asks the question instead of writing.
- Declining and cancelling are refused with the same messages as on the stateful protocol, for example `Create not performed: the client declined the confirmation prompt.`
- A client that declares only URL-mode elicitation cannot show the confirmation form, so it never sees the write tools, on either protocol. For a stateless client this is decided on every request, from the capabilities that request declares.

## Running More Than One Server Instance

!!! warning "Route each client to one instance"
    A stateless approval is held in the memory of the instance that asked, the same way query cursors are. If the retry reaches a different instance, that instance does not know the approval and refuses the retry. Nothing is written, so the failure is safe, but the client cannot complete the operation. Route each client's requests to one instance (sticky routing).

## Resource Not Found

Reading `db://schema/class/{className}` for a class that does not exist answers with JSON-RPC error `-32602` (invalid params) to a stateless client and `-32002` (resource not found) to a stateful one. The 2026-07-28 specification changed the code, and the server follows the code of the protocol the client is using.

## Server Log

For each stateless `server/discover`, the server writes one line at `INFO`:

```text
INFO  MCP client connected [stateless]: client=<name>/<version>, protocol=2026-07-28, elicitation=true, write tools exposed.
```

The server writes nothing of its own for the calls that follow. A stateful client still produces the same line once per handshake, with the connection in place of the word `stateless`. How often a stateless client sends `server/discover` again is up to the client.

## For Extension Authors

An extension write tool that calls `context.confirm(...)` works on both protocols without any change. On the stateless protocol the handler runs again from the start after the person approves, so keep side effects after `confirm()`, do not catch exceptions around it, and call it at most once per tool call: a second call in one stateless call is refused. The details are in [Write Gating for Extension Tools](extensions/index.md#write-gating-for-extension-tools).
