---
title: Actian VectorAI DB
description: Connect MCP clients to Actian VectorAI DB for semantic search over vector collections, with optional write support.
---

# Actian MCP Server for VectorAI DB

The Actian MCP Server for VectorAI DB connects AI applications to an Actian VectorAI DB engine through the open [Model Context Protocol (MCP)](https://modelcontextprotocol.io/). An MCP client sees the collections listed in the server's configuration. It can search them and page through them. When writes are enabled, it can also store or delete points after the user approves each write.

Actian VectorAI DB is the vector engine of Actian Zen AI DB. The MCP Server talks to the engine through its Representational State Transfer (REST) API (port 6573 by default). The container has no database driver.

!!! note "Four terms"
    - **Collection**: a named set of vectors on the engine; comparable to a table.
    - **Point**: one entry in a collection: an id, a vector and a payload.
    - **Payload**: the JSON stored with the point. By default the text sits in its `document` field.
    - **Embedding**: the list of numbers (vector) that a model produces for a text. Search compares the query's vector with the stored ones.

Writes are disabled by default. Setting `query_mode` to `read-write` enables them and changes which tools the server registers. See [Write support](write-support.md) and [Tools](tools/index.md).

## Capabilities

| Action | Description |
|--------|-------------|
| **Semantic search** | `search` embeds a natural-language query with the configured embedding provider and returns the nearest points with id, score, payload and text. `search_by_vector` does the same with a caller-supplied vector. |
| **Browse collections** | `list_collections` and `describe_collection` show the configured collections with their live state on the engine: existence, vector size, distance, point counts, status, payload fields. |
| **Count and page** | `count_points` and `scroll_points` accept the engine's JSON filter and page through a collection in id order. |
| **Write support** | `create_collection`, `store`, `store_batch` and `delete_points` when `query_mode` is `read-write`. Every write needs approval from the person at the MCP client. When OAuth is enabled, it also needs the `mcp:write` scope. See [Write support](write-support.md). |
| **Embedding providers** | `none` (the caller supplies the vectors), any server with the OpenAI embeddings API (Text Embeddings Inference, Ollama, vLLM, or infinity) through `base_url`, OpenAI, or Gemini. The compose file ships an optional embedding sidecar. |
| **Resources and prompts** | Health, collection list and per-collection detail as MCP resources; `find_information` and `store_information` prompts. |
| **Call log** | One JSON record per tool call in the container log, with the caller, engine, tool, and outcome. See [Call log](#call-log). |
| **Custom extensions** | Python modules mounted at `/app/extensions` add tools and resources without modifying the plugin. See [Extensions](extensions/index.md). |

This release has no MCP tool to drop a collection. Dropping a collection stays an operator action on the engine.

## Exposing Collections {#how-collections-are-exposed}

The server exposes only the collections listed under `collections` in `conf.json`. The server does not show, search, or write a collection that exists on the engine but is not listed. A tool that names it answers with the configured names instead:

```json
{"success": false, "error": "collection 'other' is not configured on this server; configured: documents, faq"}
```

A listed collection does not have to exist yet. It is reported as "not created on the engine yet" and `create_collection` creates it with the configured vector size and distance. The server never edits `conf.json`. To expose a new collection, add it to the file and restart the container.

## Prerequisites

- **Container engine:** Docker installed and running on the host.
- **Actian VectorAI DB engine:** a running engine that the container can reach over its REST API (default port 6573). The engine in an Actian Zen AI DB installation works as is. For a stand-alone engine, run the public container. The `ACTIAN_VECTORAI_ACCEPT_EULA` variable accepts the End User License Agreement (EULA): `docker run -d -e ACTIAN_VECTORAI_ACCEPT_EULA=YES -p 6573:6573 actian/vectorai:1.0.3`. Without this variable, the container exits at once.
- **Embedding endpoint (for text search and `store`):** any server that supports the OpenAI embeddings API (the compose file can start one next to the server), or an OpenAI or Gemini API key. Without one, set `embedding.provider` to `none` and use `search_by_vector` with vectors that you produce elsewhere.
- **Engine API key (optional):** only when authentication is turned on in the engine. See [Engine API key](#engine-api-key).
- **OpenID Connect (OIDC) provider (optional):** only when you use OAuth. See [Authentication](authentication/index.md).

!!! note "Startup needs the engine"
    The server checks the engine once at start. It refuses to run when the engine does not answer. With `docker run --restart unless-stopped` or compose, the container restarts until the engine is reachable, and the log shows `RuntimeError: VectorAI engine at <url> is unreachable`. Start the engine first.

## Configuration

Configuration is a `conf.json` file mounted at `/app/conf.json`. Framework keys (`host`, `port`, `query_mode`, `write_confirmation`, `log_level`, `oauth`, `auth_mode`, `extensions`) work as for every other plugin. The VectorAI plugin adds three blocks: `vectorai` (where the engine is), `embedding` (how text becomes vectors) and `collections` (what is exposed).

Minimal, read-only, vectors supplied by the caller:

```json
{
    "host": "0.0.0.0",
    "port": 8000,
    "query_mode": "read-only",
    "vectorai": { "url": "http://host.docker.internal:6573" },
    "embedding": { "provider": "none" },
    "collections": [
        { "name": "documents", "description": "Product manuals, one chunk per point" }
    ]
}
```

Read-write with the embedding sidecar from the compose file (`conf.sidecar.json` in the image sources):

```json
{
    "host": "0.0.0.0",
    "port": 8000,
    "query_mode": "read-write",
    "vectorai": { "url": "http://host.docker.internal:6573" },
    "embedding": {
        "provider": "openai",
        "model": "BAAI/bge-m3",
        "base_url": "http://embedding:80/v1",
        "max_input_tokens": 8192
    },
    "collections": [
        { "name": "documents", "description": "Product manuals, one chunk per point" },
        { "name": "faq", "description": "Support FAQ", "text_field": "answer" }
    ]
}
```

Hosted provider with a key:

```json
"embedding": { "provider": "openai", "model": "text-embedding-3-small", "api_key_secret": "<API_KEY>" }
```

The key can also come from the environment variable `VECTORAI_EMBEDDING_API_KEY` instead of the file. Keys in `conf.json` end in `_secret` so the server's debug output redacts them.

### Engine API Key

The engine ships with authentication off. It answers every REST request, and the server needs no key. When authentication is on, every request must carry a key. The server sends the value of `vectorai.api_key_secret` (or the environment variable `VECTORAI_API_KEY`) as the `api-key` header on every call, including the startup check and the health resource.

You turn authentication on in the engine, not in the MCP Server. For the `actian/vectorai` container, do the following. Start it with `ACTIAN_VECTORAI_ADMIN_PASSWORD=<password>`, which creates the built-in `admin` user. Sign in with `POST /auth/admin/login` to get an admin token. Enable authentication with `PATCH /auth/enabled` and body `{"enabled": true}`. Then create a key with `POST /auth/api_key` and permission `read` (read-only server) or `read,write`. The engine keeps the setting across restarts. The engine documentation calls these keys access tokens. For the full API, including expiry and permissions, see [Create access token](https://docs.vectoraidb.actian.com/api-reference/access-tokens/create-access-token) in the Actian VectorAI DB documentation.

### One Embedding Model per Collection

The engine stores vectors, not the name of the model that produced them. A collection filled with one model and searched with another returns meaningless scores. Keep `embedding.model` (or the per-collection override) the same for the life of a collection. For a collection that already exists, set `vector_size` in `conf.json` so that the server reports a mismatch instead of returning bad results. `store` and `store_batch` compare the embedding's dimension with the collection's before anything is written.

### Configuration Reference

**Framework keys**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `host` | string | Yes | — | Bind address inside the container. Use `0.0.0.0` so the server is reachable from outside the container. |
| `port` | integer | Yes | — | Port the server listens on. Must match the port Docker exposes. |
| `query_mode` | string | No | `read-only` | `read-only` or `read-write`. Determines which tools and prompts are registered. See [Write support](write-support.md). |
| `write_confirmation` | boolean | No | `true` | When `false`, write tools run without the human approval prompt. The `mcp:write` scope check still applies. Only relevant in `read-write`. |
| `log_level` | string | No | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |
| `oauth` | object | No | — | OAuth configuration for protected deployments. See [Authentication](authentication/index.md). |
| `auth_mode` | string | No | — | `resource-server` makes the server verify tokens that the identity provider issues instead of running its own login. See [Resource-server mode](authentication/index.md#resource-server-mode). |
| `ssl_certfile`, `ssl_keyfile` | string | No | — | In-container paths of the TLS certificate and key, `/app/server.crt` and `/app/server.key`. Required whenever OAuth is on and `host` is not `localhost`. See [HTTPS and TLS](authentication/index.md#secure-remote-deployments-with-https-and-tls). |
| `extensions` | array | No | — | Extension modules to load. See [Extensions](extensions/index.md). |

**Engine connection, block `vectorai`**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `vectorai.url` | string | No | `http://127.0.0.1:6573` | REST base URL of the engine. From a container the host engine is `http://host.docker.internal:6573`. |
| `vectorai.api_key_secret` | string | No | — | Sent as the `api-key` header on every request. Alternative: environment variable `VECTORAI_API_KEY`. The server warns at startup when the key travels over plain `http://` to another host. |
| `vectorai.timeout` | number | No | `30` | Seconds per request. |
| `vectorai.retry_max` | integer | No | `3` | Retries on retryable statuses and network errors. |
| `vectorai.retry_on_status` | array | No | `[408, 429, 500, 502, 503, 504]` | HTTP statuses that are retried. `Retry-After` is honored. |
| `vectorai.backoff_base`, `vectorai.backoff_max` | number | No | `1`, `30` | Exponential backoff with full jitter, in seconds. |
| `vectorai.ca_file` | string | No | — | PEM bundle for an `https://` engine behind a private certificate authority. |

**Text embedding, block `embedding`** (the default for all collections; a collection may override it)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `embedding.provider` | string | No | `none` | `none`, `openai`, `gemini`, or `dev-hash`. `none` disables `search`, `store` and `store_batch`; `search_by_vector` still works. `dev-hash` is a deterministic test provider, not a semantic embedding, and the log says so. |
| `embedding.model` | string | With `base_url` | `text-embedding-3-small` (openai), `gemini-embedding-001` (gemini) | Model name. With `base_url`, this is the model that the endpoint serves, and it is required. |
| `embedding.base_url` | string | No | — | OpenAI-compatible endpoint, for example `http://embedding:80/v1` for the compose sidecar or `http://host.docker.internal:11434/v1` for Ollama. It makes the API key optional. |
| `embedding.api_key_secret` | string | For hosted providers | — | Provider key. Alternative: environment variable `VECTORAI_EMBEDDING_API_KEY`. Required for `gemini`, and for `openai` without `base_url`. |
| `embedding.vector_size` | integer | For `dev-hash` | — | Vector dimension. For `openai` it is passed as `dimensions` (models that support shortening). Otherwise the provider's dimension is used. Do not set it for models that do not support shortening. The vector is cut, and search quality drops without a warning. |
| `embedding.batch_size` | integer | No | `32` | Texts per embedding request in `store_batch`. |
| `embedding.max_input_tokens` | integer | No | `8191` for hosted OpenAI, unset otherwise | Token limit of the served model. The server refuses a text that reaches the limit before the approval prompt, instead of cutting it. Set it for a self-hosted endpoint (8192 for bge-m3, 512 for bge-small-en-v1.5). |
| `embedding.ca_file` | string | No | — | PEM bundle for an `https://` endpoint behind a private certificate authority. |

**Collections, list `collections`** (required, at least one entry; a plain string is a name with defaults)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `collections[].name` | string | Yes | — | Collection name on the engine, 1 to 255 characters, none of `< > : " / \ \| ? *`. Listed once. |
| `collections[].description` | string | No | empty | Shown to the model in the server instructions and in `list_collections`. The engine itself stores no description. |
| `collections[].vector_size` | integer | No | provider's dimension | Used by `create_collection`; checked against the engine on every listing (a mismatch adds a `warning`). Required when `embedding.provider` is `none` and the collection does not exist yet. |
| `collections[].distance` | string | No | `Cosine` | `Cosine`, `Dot`, `Euclid`, or `Manhattan`. Used by `create_collection`. |
| `collections[].embedding` | object | No | the top-level block | Per-collection override. The same provider merges with the top-level block; a different provider replaces it entirely. |
| `collections[].text_field` | string | No | `document` | Payload field that holds the text. `store` writes the text there; `search` and `scroll_points` return it as `text`. |

**Limits**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `search_limit` | integer | No | `10` | Default `limit` for `search`, `search_by_vector` and `scroll_points`. |
| `max_search_limit` | integer | No | `100` | Upper bound for `limit`; larger requests are capped, not rejected, and the response reports the effective `limit`. Must be at least `search_limit`. |
| `max_batch_size` | integer | No | `32` | Maximum items in one `store_batch` call. The server rejects a longer batch before the approval prompt. |

**Call log**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `call_log` | boolean | No | `true` | One JSON record per tool call in the container log. See [Call log](#call-log). |
| `call_log_queries` | boolean | No | `false` | Adds the `search` query text to the record as `query`. The server logs a warning at every start while this is on. |

Not used by this plugin: `conn_string`, `database`, `username`, `password`, `max_rows`. The server refuses a `targets` block (several databases from one server) at startup. It supports one engine per server.

## Start Server {#start-the-server}

Once `conf.json` is ready, start the container and mount the configuration file:

```bash
docker run -d \
  --name vectorai-mcp \
  -p 8000:8000 \
  --add-host=host.docker.internal:host-gateway \
  -v $(pwd)/conf.json:/app/conf.json:ro \
  actian/vectorai-mcp-server:1.2.0
```

The MCP endpoint is `http://<host>:8000/mcp` (streamable HTTP).

!!! note "Container networking"
    `-p 8000:8000` exposes the server port on the host. `--add-host=host.docker.internal:host-gateway` lets the container reach services on the host machine (such as the engine on port 6573). Docker Desktop on Windows and macOS resolves `host.docker.internal` automatically. Linux requires the `--add-host` flag.

With the embedding sidecar, use the compose file shipped with the image sources (`src/vectorai/docker/docker-compose.yml`):

```bash
CONF_FILE=./conf.json docker compose --profile embedding up -d
```

This starts Text Embeddings Inference (CPU build) with `BAAI/bge-m3` next to the server. It downloads the model once into the `tei-cache` volume (2.2 GB). The sidecar reports `healthy` a few minutes after the first start. Point `embedding.base_url` at `http://embedding:80/v1` and set `embedding.model` to the same model name. For another model, set `EMBEDDING_MODEL=<huggingface id>`. bge-m3 is multilingual. `BAAI/bge-small-en-v1.5` is English-only. The sidecar runs with `AUTO_TRUNCATE=false`, so it refuses a text that is longer than the model accepts instead of cutting it.

Wait for these log lines: the engine check, `VectorAI: <engine version> at <url>, N/M configured collection(s) present, mode=read-only`, and then `Uvicorn running on http://0.0.0.0:8000`.

## Usage

The server instructions that the client receives include the collection summary: name, description, vector size and distance, point count, and which embedding answers text search (or "no text embedding: use search_by_vector"). Typical workflows:

- **Find, then search:** `list_collections`, then `search` on the collection whose description fits the question. Scores are the engine's similarity scores; `score_threshold` cuts off weak matches.
- **Filter:** restrict a search with the engine's JSON filter on payload fields, for example `{"must": [{"key": "metadata.kind", "match": {"value": "faq"}}]}`. The same filter works in `count_points` and `scroll_points`. The server passes the filter to the engine unchanged. For the syntax, see the Actian VectorAI DB documentation.
- **Write:** in `read-write` mode, run `create_collection` once. Then use `store` for one text per call or `store_batch` for several, with `metadata` for later filtering. Each call asks the person at the client for approval.

When OAuth is enabled, the token protects the MCP Server. The engine `api-key` is a separate secret that the server sends to the engine for every caller. The plugin does not impersonate users at the engine.

### Engine Behavior {#engine-behaviour}

- Until the engine loads a collection for a search, the collection shows `points_count: 0` with a non-zero `vectors_count` and the status `unknowncollectionstatus`. `count_points` is always exact.
- A collection with mostly deleted points reports `status: "red"` (delete ratio above one half), or `"yellow"` above 0.3. This is not an error. Searches and writes keep working, and the status returns to `green` as you add live points. A rebuild of the index also shows `yellow`.
- Point ids are either UUID strings or unsigned integers. `store` generates a UUID when you give none. It overwrites an existing id, and the approval prompt says so.
- The engine stores no description per collection (its REST `metadata` on create answers 501). The description shown to the model comes from `conf.json`.

## Call Log

Every tool call writes one JSON line to the container log (`docker logs <container>`). The record has the same fields as the Zen plugin's call log, so one log pipeline serves both:

```json
{"ts": "2026-11-12T16:08:34.379+00:00", "user": "mcp_test_user", "target": "http://127.0.0.1:6573",
 "tool": "store", "action": "write", "status": "ok", "rows": 1, "latency_ms": 11.7,
 "correlation_id": "eb5bb698bc6d43488482a85dd968aa92", "request_id": "1",
 "detail": {"collection": "rs_probe"}}
```

| Field | Meaning |
|-------|---------|
| `user` | The user named by the access token; `null` without OAuth or for a token that names no user. The engine itself only sees the server's API key, so this is where a deployment records who asked. |
| `target` | The engine URL (scheme, host, port). |
| `action` | `read` for the six read tools, `write` for `store`, `store_batch` and `delete_points`, `admin` for `create_collection`. |
| `status` | `ok`; `error` for an engine or validation error or a token without `mcp:write`; `rejected` when the approver declined. |
| `rows` | Results, points or collections returned; points stored or deleted; a count. `null` where nothing countable was returned. |
| `correlation_id`, `request_id` | The MCP session and request ids, for matching records to a client conversation. |
| `detail` | The collection, and the number of `ids` or `items` the call named. |

Query text, payloads, vectors and filter values are never written. `call_log_queries` adds the `search` query text; `call_log: false` turns the log off. The log is a record of what the server did, not an audit trail: nothing in it is tamper-evident.

## Authentication

The server supports the same modes as every other plugin. See [Authentication](authentication/index.md). VectorAI DB differs from the SQL plugins in one way: it has no per-user database identity. Every engine request carries the configured API key. So `user_impersonation` only decides where the server looks for the caller's name for the call log. In resource-server mode, it also decides whether a token must name a user. There, the default `true` refuses a token without a `username`, `preferred_username`, or `email` claim, and `false` accepts service tokens too. [User Impersonation](authentication/index.md#user-impersonation) has the details for each mode. `conf.resource-server.json` in the image's docker folder is a filled-in `resource-server` example with `user_impersonation: false`.

Reads need a valid token for the server's audience. Writes also need the `mcp:write` scope. The server checks the scope before any embedding call, and then shows the approval prompt.

## Next Steps

<div class="grid cards" markdown>

- :material-pencil: **[Write Support](write-support.md)**  
  Enable writes and see what gates each write.

- :material-lock: **[Authentication](authentication/index.md)**  
  Secure the server with OAuth 2.0 and an external identity provider.

- :material-tools: **[Tools](tools/index.md)**  
  Parameters and output of the six read tools and the four write tools.

- :material-folder-open: **[Resources](resources/index.md)**  
  Engine health and collection state as MCP resources.

- :material-message-text: **[Prompts](prompts/index.md)**  
  Use the built-in prompt templates for finding and storing information.

- :material-puzzle: **[Extensions](extensions/index.md)**  
  Add custom tools to the server with a Python extension.

</div>
