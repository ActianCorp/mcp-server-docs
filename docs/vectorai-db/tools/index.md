---
title: Tools
description: Reference for the VectorAI DB tools of the Actian MCP Server: collection listing, semantic search, counting, paging, and the gated write tools.
---

# Tools

The server registers six read tools in every mode and four write tools only when `query_mode` is `read-write` (see [Write support](../write-support.md)). Every tool except `list_collections` takes a `collection` name and answers only for collections listed in `conf.json`; any other name returns an error that lists the configured ones.

## Available Tools

| Tool | read-only | read-write | Description |
|------|-----------|------------|-------------|
| [`list_collections`](#list_collections) | yes | yes | Configured collections with their live state on the engine. |
| [`describe_collection`](#describe_collection) | yes | yes | Full detail for one collection: engine config, payload schema, index type. |
| [`search`](#search) | yes | yes | Semantic search from a text query. |
| [`search_by_vector`](#search_by_vector) | yes | yes | Nearest-neighbour search from a vector. |
| [`count_points`](#count_points) | yes | yes | Number of points, optionally filtered. |
| [`scroll_points`](#scroll_points) | yes | yes | Page through points in id order. |
| [`create_collection`](#create_collection) | | yes | Create a configured collection on the engine. |
| [`store`](#store) | | yes | Embed one text and store it as a point. |
| [`store_batch`](#store_batch) | | yes | Embed several texts and store them as points with one approval. |
| [`delete_points`](#delete_points) | | yes | Delete points by id. |

Writes require the `mcp:write` scope when OAuth is enabled and an approval prompt at the client. `search`, `store` and `store_batch` need an embedding provider. With `embedding.provider: none` they answer with an error; use `search_by_vector` instead.

### Common Output

Every tool returns a JSON object with `success`. On failure:

```json
{
  "success": false,
  "error": "<message>",
  "status_code": 404
}
```

`status_code` is present when the engine answered with an HTTP error (the message is then prefixed `VectorAI:`, for example `VectorAI: Search failed: Dimension mismatch for vector '': expected 1024, got 2`). Other errors are validation errors (`limit must be >= 1`, `text must not be empty`, `collection 'x' is not configured on this server; configured: ...`), embedding errors, or `Write rejected by user`.

### Filters

`search`, `search_by_vector`, `count_points` and `scroll_points` accept `filter`, the engine's JSON filter on payload fields, passed through unchanged:

```json
{"must": [{"key": "metadata.kind", "match": {"value": "faq"}}]}
```

`store` writes `metadata` under the payload key `metadata`, so fields given at store time are addressed as `metadata.<field>`. See the Actian VectorAI DB documentation on filtering for the full syntax.

---

## `list_collections`

Returns the collections this server exposes with their live state. Only these collections can be searched or written.

This tool takes no input parameters.

**Output schema**

```json
{
  "success": true,
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
      "payload_fields": ["document", "metadata"],
      "warning": "<only when conf.json vector_size differs from the engine's>"
    },
    {
      "name": "<name>",
      "description": "<from conf.json>",
      "text_field": "document",
      "embedding": { "provider": "none" },
      "exists": false
    }
  ]
}
```

`exists` is `false` for a configured collection not yet created on the engine, and `null` with an `error` field when the engine could not answer for it. `status` is the engine's collection status: `green`, `yellow`, `red`, or `unknowncollectionstatus` for a collection the engine has not loaded yet; see [Engine behaviour](../index.md#engine-behaviour).

---

## `describe_collection`

Full detail for one configured collection: everything `list_collections` shows plus the engine's configuration, payload schema and index type, and the values configured in `conf.json`.

**Parameters**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `collection` | string | Yes | A configured collection name. |

**Output schema**

```json
{
  "success": true,
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
  "payload_fields": ["document", "metadata"],
  "engine_config": { "<the engine's collection config, as returned by GET /collections/{name}>": "..." },
  "payload_schema": { "<payload field>": { "<the engine's schema entry for the field>": "..." } },
  "index_type": "<engine index type>",
  "configured": { "vector_size": 1024, "distance": "Cosine" }
}
```

`engine_config`, `payload_schema` and `index_type` are absent when the collection does not exist yet.

---

## `search`

Embeds `query` with the collection's embedding provider and returns the nearest points.

**Parameters**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `collection` | string | Yes | | A configured collection name. |
| `query` | string | Yes | | Natural-language query text. |
| `limit` | integer | No | `search_limit` (10) | Number of results, at least 1, capped at `max_search_limit` (100). |
| `filter` | object | No | — | Engine JSON filter on payload fields. |
| `score_threshold` | number | No | — | Drop results scoring below this value. |

**Output schema**

```json
{
  "success": true,
  "collection": "<name>",
  "count": 3,
  "limit": 10,
  "results": [
    {
      "id": "bc81fbea-12a8-4296-b156-bd6d23ec5764",
      "score": 0.6556,
      "payload": { "document": "<text>", "metadata": { "kind": "faq" } },
      "text": "<text>"
    }
  ]
}
```

`text` is the payload's `text_field` and is present only when that field exists on the point. `count` is the number of results returned, `limit` the effective limit after capping: a request with `limit: 100000` comes back with `"limit": 100`.

**Example**

Request:

```json
{ "collection": "documents", "query": "how do I enable write mode", "limit": 3 }
```

Response (abridged):

```json
{ "success": true, "collection": "documents", "count": 3, "limit": 3,
  "results": [ { "id": "7e1c...", "score": 0.71, "text": "Set query_mode to read-write in conf.json ...", "payload": { "document": "Set query_mode ...", "metadata": { "source": "write-support.md" } } }, "..." ] }
```

---

## `search_by_vector`

Nearest-neighbour search with a vector the caller already has. The vector must have the collection's dimension; the engine refuses any other size (`Dimension mismatch ... expected 1024, got 2`). Works with `embedding.provider: none`.

**Parameters**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `collection` | string | Yes | | A configured collection name. |
| `vector` | array of numbers | Yes | | Query vector, same dimension as the collection; must not be empty. |
| `limit` | integer | No | `search_limit` (10) | As for `search`. |
| `filter` | object | No | — | As for `search`. |
| `score_threshold` | number | No | — | As for `search`. |

**Output schema**: same as `search`.

---

## `count_points`

Number of points in a configured collection, optionally restricted by a filter. Exact at any time (unlike the `points_count` shown by `list_collections` before the engine has loaded the collection).

**Parameters**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `collection` | string | Yes | A configured collection name. |
| `filter` | object | No | Engine JSON filter. |

**Output schema**

```json
{ "success": true, "collection": "<name>", "count": 186 }
```

---

## `scroll_points`

Pages through a collection's points in id order without a query vector. Pass the returned `next_page_offset` as `offset` to get the next page; it is `null` on the last page.

**Parameters**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `collection` | string | Yes | | A configured collection name. |
| `limit` | integer | No | `search_limit` (10) | Page size, capped at `max_search_limit`. |
| `offset` | integer or string | No | — | The `next_page_offset` of the previous page. |
| `filter` | object | No | — | Engine JSON filter. |
| `with_vector` | boolean | No | `false` | Include each point's stored vector in the output. A page with vectors is capped at 10 points. |

**Output schema**

```json
{
  "success": true,
  "collection": "<name>",
  "limit": 10,
  "points": [
    { "id": 12, "score": null, "payload": { "document": "<text>" }, "text": "<text>",
      "vector": [0.0123, -0.0456, "..."] }
  ],
  "next_page_offset": 42
}
```

`score` is always `null` for scrolled points (no query vector). `vector` is present only when `with_vector` is `true`; it has the collection's dimension.

---

## `create_collection`

Read-write mode only. Creates a configured collection on the engine with the configured `vector_size` and `distance` (`Cosine` when unset). When `vector_size` is not in `conf.json`, the embedding provider's dimension is used; for providers that do not publish it, one probe embedding is made. When the collection already exists the call succeeds without a prompt and without changes.

**Parameters**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `collection` | string | Yes | A configured collection name. |

**Approval prompt**: `Create collection <name> (<size>-dim, <distance>)`.

**Output schema**

```json
{ "success": true, "collection": "<name>", "created": true, "vector_size": 1024, "distance": "Cosine" }
```

```json
{ "success": true, "collection": "<name>", "created": false, "message": "collection already exists" }
```

A collection with `embedding.provider: none` and no `vector_size` cannot be created: the error says which key to add to `conf.json`.

---

## `store`

Read-write mode only. Embeds `text` and upserts it as one point. The payload holds the text under the collection's `text_field` (default `document`) plus `metadata` as given, so later filters can use `metadata.<field>`. The collection must already exist.

Before asking for approval, `store` checks that the text is not empty, that the collection exists on the engine, that the text is within `embedding.max_input_tokens` when that is set, and that the embedding's dimension equals the collection's vector size. A mismatch is reported as an error naming the two sizes and the `conf.json` keys to fix. The text reaches the embedding provider before the prompt.

**Parameters**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `collection` | string | Yes | | A configured collection name. |
| `text` | string | Yes | | The text to embed and store; must not be blank. |
| `metadata` | object | No | — | Stored under the payload key `metadata`. |
| `id` | string or integer | No | new UUID | UUID string or unsigned integer. An existing id is overwritten. |

**Approval prompt**: `Store 1 point in <name>: <first 120 characters of the text>`, plus `overwrites existing point <id>` when the id already exists. The prompt details carry the id, the text preview, the metadata, the ids overwritten and the vector size.

**Output schema**

```json
{
  "success": true,
  "collection": "<name>",
  "id": "bc81fbea-12a8-4296-b156-bd6d23ec5764",
  "operation": { "operation_id": 0, "status": "Completed" }
}
```

`operation` is the engine's response to the upsert.

**Example**

Request:

```json
{ "collection": "documents", "text": "Write tools require the user to approve each change.", "metadata": { "kind": "note" } }
```

The client shows `Store 1 point in documents: Write tools require the user to approve each change.`; after approval the response above is returned.

---

## `store_batch`

Read-write mode only. Embeds several texts and upserts them as points in one call, with one approval prompt for the whole batch. The texts go to the embedding provider in requests of `embedding.batch_size` and to the engine in one request, so all points land or none. Each item takes the same fields as a `store` call.

Before asking for approval, `store_batch` checks every item (text not blank, `id` a UUID string or unsigned integer and used once in the batch, `metadata` an object), that the collection exists on the engine, that no text exceeds `embedding.max_input_tokens` when that is set, and that the embeddings' dimension equals the collection's vector size. A batch longer than `max_batch_size` (default 32) is rejected as well: `store_batch takes at most 32 items per call, got 40; split the batch or raise max_batch_size in conf.json`. Any failure returns an error and nothing is written.

**Parameters**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `collection` | string | Yes | A configured collection name. |
| `items` | array of objects | Yes | 1 to `max_batch_size` items, each `{"text": string, "metadata"?: object, "id"?: string or integer}`. A missing id becomes a new UUID; an existing id is overwritten. |

**Approval prompt**: a header `Store <n> points in <name>: <total> chars, metadata keys: <keys>` (or `no metadata`), with `overwrites <k> existing points` appended when ids already exist, followed by one numbered line per item: its length, its metadata, the first 60 characters of the text, and `overwrites id <id>` where applicable. The approver sees every item, because one approval covers the whole batch. The details carry all ids, the ids overwritten, the count, the total characters, the metadata keys and the vector size.

**Output schema**

```json
{
  "success": true,
  "collection": "<name>",
  "stored": 3,
  "ids": [7, "bc81fbea-12a8-4296-b156-bd6d23ec5764", "0f3c9d2a-7b1e-4c55-9a0d-5e6f7a8b9c0d"],
  "operation": { "operation_id": 0, "status": "Completed" }
}
```

`ids` is in item order, so a wrong batch is undone with one `delete_points` call. Loading a whole corpus still belongs in a script against the engine's REST API, not in an MCP session.

---

## `delete_points`

Read-write mode only. Deletes points by id from a configured collection. The server looks the ids up first: `deleted` counts the ids that existed, the rest come back in `not_found`. When none of the ids exist nothing is deleted and no approval is asked.

**Parameters**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `collection` | string | Yes | A configured collection name. |
| `ids` | array of string or integer | Yes | Point ids; must not be empty. A UUID is accepted in any spelling (case, with or without hyphens). |

**Approval prompt**: `Delete <n> points from <name>`, with `(<k> of <m> requested ids not found)` appended when some ids do not exist; the details list the first 20 ids to delete and the ids not found.

**Output schema**

```json
{
  "success": true,
  "collection": "<name>",
  "deleted": 2,
  "not_found": [],
  "operation": { "operation_id": 0, "status": "Completed" }
}
```

```json
{ "success": true, "collection": "<name>", "deleted": 0, "not_found": [9001, 9002], "message": "none of the ids exist, nothing to delete" }
```

A collection left with few live points shows `status: "red"` until new points are added (see [Engine behaviour](../index.md#engine-behaviour)).

## Next Steps

- [Resources](../resources/index.md): the same collection information as MCP resources.
- [Prompts](../prompts/index.md): `find_information` and `store_information`.
- [Write support](../write-support.md): enabling writes and the approval flow.
