---
title: Resources
description: MCP resources of the Actian MCP Server for VectorAI DB - engine health, the configured collections and per-collection detail.
---

# Resources

The Actian MCP Server for VectorAI DB publishes three JSON resources so a client can read the engine state and the collection summary without calling tools. They are available in both query modes.

## Available resources

| Resource URI | Description |
|--------------|-------------|
| `resource://vectorai/health` | Engine identity and `/healthz` state. |
| `resource://vectorai/collections` | Configured collections with their live engine state. |
| `resource://vectorai/collections/{name}` | Detail for one configured collection. |

---

## `resource://vectorai/health`

The engine's root response (its identity and version) and whether its `/healthz` endpoint answers.

**Parameters**: none.

**Output schema**

```json
{
  "url": "http://host.docker.internal:6573",
  "engine": { "title": "Actian VectorAI DB", "version": "Actian VectorAI DB 1.0.3", "commit": "8d222ff5" },
  "healthz": true
}
```

When the engine does not answer, `engine` is `{ "error": "<message>" }` and `healthz` is `false`.

---

## `resource://vectorai/collections`

The same list as the `list_collections` tool.

**Parameters**: none.

**Output schema**

```json
{
  "collections": [
    {
      "name": "<name>",
      "description": "<from conf.json>",
      "text_field": "document",
      "embedding": { "provider": "openai", "model": "BAAI/bge-m3" },
      "exists": true,
      "vector_size": 1024,
      "distance": "Cosine",
      "points_count": 186,
      "vectors_count": 186,
      "status": "green",
      "payload_fields": ["document", "metadata"]
    }
  ]
}
```

See the [`list_collections`](../tools/index.md#list_collections) tool for the meaning of `exists`, `status` and `warning`.

---

## `resource://vectorai/collections/{name}`

The same detail as the `describe_collection` tool.

**Parameters**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | A configured collection name. |

**Output schema**: the [`describe_collection`](../tools/index.md#describe_collection) output without the `success` field. For a name that is not configured, or when the engine fails:

```json
{ "error": "collection 'other' is not configured on this server; configured: documents, faq" }
```

## Next steps

- [Tools](../tools/index.md): `list_collections` and `describe_collection`.
- [Prompts](../prompts/index.md).
