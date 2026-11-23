---
title: Write Support
description: Enable write operations in the Actian MCP Server for VectorAI DB, and what gates each write: the mcp:write scope and the human approval prompt.
---

# Write Support

By default, the Actian MCP Server for VectorAI DB permits only reads: listing, searching, counting and paging. Set `query_mode` to `read-write` in `conf.json` to also register the four write tools: `create_collection`, `store`, `store_batch` and `delete_points`. Extensions can write through the same checks.

## Write Operations in VectorAI DB {#what-a-write-is-in-vectorai}

| Tool | Writes | Approval text shown to the user |
|------|--------|---------------------------------|
| `create_collection` | Creates a configured collection on the engine with its configured vector size and distance. A second call on an existing collection succeeds without a prompt. | `Create collection <name> (<size>-dim, <distance>)` |
| `store` | Embeds one text and upserts it as one point (text under the collection's `text_field`, plus `metadata`). An existing id is overwritten. | `Store 1 point in <name>: <first 120 characters>`, plus `overwrites existing point <id>` when the id exists |
| `store_batch` | Embeds several texts and upserts them as points in one engine request. Same item rules as `store`; at most `max_batch_size` items (default 32). | `Store <n> points in <name>: <total> chars, metadata keys: <keys>` followed by one line per item (length, metadata, first 60 characters, overwrite marker) |
| `delete_points` | Deletes the points whose ids exist; the rest are reported as `not_found`. Nothing to delete means no prompt. | `Delete <n> points from <name>`, plus `(<k> of <m> requested ids not found)` |

Every prompt is sent as `Approve this database write?`, the text above, and a `Details` block in JSON (collection, ids, vector size, and for batches every id and the ids overwritten). The client shows it to the person and returns their answer.

Only collections listed in `conf.json` can be created or written. Dropping a collection is not an MCP tool; it stays an operator action against the engine (`DELETE /collections/<name>` on the REST API). Payload updates without re-embedding are not part of this release. `store_batch` stores several texts with one approval, at most `max_batch_size` items (32 by default). Loading a whole corpus belongs in a script against the engine, not in an MCP session.

## Enabling Write Mode

| Value | Behavior |
|-------|-----------|
| `read-only` (default) | Read tools and the `find_information` prompt only. Write tools are not registered, so clients never see them. |
| `read-write` | Read tools plus `create_collection`, `store`, `store_batch`, `delete_points` and the `store_information` prompt. |

## Authorizing a Write

Every write passes two independent checks before it reaches the engine.

| Check | What it requires | When it applies |
|-------|------------------|-----------------|
| OAuth scope | The access token must carry the `mcp:write` scope. | Only when OAuth is enabled. A read-only server never requests or requires this scope. |
| Human approval | The MCP client shows the approval text above and a person accepts it. | Always in `read-write`, unless `write_confirmation` is `false`. |

The scope is checked first, before any text is sent to the embedding provider, so a caller without it is rejected before anyone is asked to approve anything:

```json
{"success": false, "error": "write operations require the 'mcp:write' scope, which the access token does not carry"}
```

A declined prompt, a prompt not answered within 60 seconds, or a client that cannot show prompts all result in `Write rejected by user`; nothing is written. Every outcome leaves one call log record: `status: "ok"` for a write that landed, `"rejected"` for a declined prompt, `"error"` for a missing scope or a validation failure, with the token's user in `user` (see [Call log](index.md#call-log)).

`store` and `store_batch` validate before they ask: the collection must exist on the engine, no text may be empty, ids must be UUID strings or unsigned integers (and unique within a batch), the batch may not exceed `max_batch_size`, a text may not reach `embedding.max_input_tokens` when that is set, and the embedding's dimension must match the collection's vector size. Those failures come back as errors without an approval prompt, so the user is never asked to approve a write that cannot land.

!!! note "Text leaves the server before the prompt"
    The dimension check needs the vector, so the text goes to the embedding provider before the approval prompt. With `openai` or `gemini` on a hosted endpoint the text has left the host even when the write is then declined; a sidecar through `embedding.base_url` keeps it on the network; `none` and `dev-hash` send nothing.

## Skipping Approval Prompt {#skipping-the-approval-prompt}

For clients that cannot show an approval prompt, set `write_confirmation` to `false` in `conf.json`. The write tools then run without asking, and the server logs every such write as `WRITE EXECUTED WITHOUT CONFIRMATION`. The `mcp:write` scope check still applies: disabling the prompt does not grant write access to callers that lack the scope.

This removes human oversight of every write. Use it only where the client is itself an automated, trusted pipeline.

## Next Steps

- [Configuration](index.md#configuration): `query_mode`, `write_confirmation`, `collections`, `max_batch_size`.
- [Authentication](authentication/index.md): granting the `mcp:write` scope in Auth0 and Keycloak.
- [Tools](tools/index.md): parameters and output of the four write tools.
