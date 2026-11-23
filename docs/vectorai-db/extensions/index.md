---
title: Extensions
description: Add your own tools, resources, and prompts to the Actian MCP Server by writing a Python extension module.
---

# Extensions

You can extend the Actian MCP Server with **extensions**: your own Python modules that register extra tools, resources, and prompts on the running server, next to the built-in database tools. Use this for business logic you want an AI agent to call through the same endpoint, such as revenue forecasting, compliance checks, or data enrichment.

An extension *adds* capabilities. It does not manage the engine connection: the server already talks to the engine and already exposes the built-in tools. The module provides a `register()` function and uses the extension API for the caller's identity, scopes and the approval prompt.

Extensions are supported on Actian VectorAI DB.

## Writing Module {#writing-the-module}

An extension is a normal Python module exposing one required function and two optional hooks:

```python
from actian_mcp_server.extension_api import (
    get_current_user,            # authenticated identity, or None
    has_scope,                   # does the caller's token carry a scope
    request_write_confirmation,  # opt-in human approval gate
)

def register(server, config):          # REQUIRED, synchronous
    @server.tool(name="my_tool")
    async def my_tool(x: str) -> str:
        user = get_current_user()
        return "result"

async def setup(config): ...           # OPTIONAL, open resources at startup
async def teardown(): ...              # OPTIONAL, release them at shutdown
```

`register(server, config)` is called once at startup. Register your tools, resources, and prompts there exactly as you would on any FastMCP server.

Implement `setup(config)` and `teardown()` only if your extension owns something that needs an explicit open and close, such as an HTTP client, a cache, or a connection pool of your own. Either may be `async` or plain.

!!! note "Configuration never contains secrets"
    The `config` argument holds the `config` block you set in `conf.json` plus a short list of non-secret values (`dbms`, `max_rows`, `transport`). It never contains the engine API key, the embedding key or OAuth secrets.

Give your tools schema-friendly signatures: typed parameters, and no `*args` or `**kwargs`.

## Mounting and Registering Module {#mounting-and-registering-the-module}

Mount your module into the server's extensions directory, `/app/extensions`, as a volume. The server makes that directory importable:

```bash
docker run -d \
    -v ./revenue_forecast.py:/app/extensions/revenue_forecast.py:ro \
    -v ./conf.json:/app/conf.json:ro \
    -p 8000:8000 \
    <actian-mcp-image>
```

Then list it by module name in `conf.json`. Paths are not used, because the location is fixed:

```json
{
  "extensions": [
    { "module": "simple_extension" },
    {
      "module": "revenue_forecast",
      "config": { "api_url": "https://forecast.example.com", "timeout": 20 }
    }
  ]
}
```

| Rule | Detail |
|------|--------|
| Entry shape | An object with a required `module` and an optional `config`. Omit `config` if the extension needs no settings. |
| Module name | The name of the file or package you mounted, for example `revenue_forecast.py` or `revenue_forecast/`. A package works by its dotted import path, such as `my_package.my_module`. |
| Order | Extensions load in the order listed. Each module may be listed only once. |

## Server Responsibilities

| Concern | How it is handled |
|---------|-------------------|
| Authentication | The user is authenticated before your code runs. Read the identity with `get_current_user()`. |
| Error isolation | An exception in your tool is returned to the client as an error. It does not crash the server. |
| Transport and protocol | The server serves MCP over HTTP. You do not implement any of it. |
| Logging | Extension loading, tool registration, and approval outcomes go to the server log, and so do your own `logging.getLogger(__name__)` messages. There is no automatic per-call audit log. If you need a record of who called what, log it in your tool. |

## Reaching Engine {#reaching-the-engine}

The extension API's `get_database()` runs SQL and exists for the SQL plugins. On a VectorAI DB server its `query()` answers `{"success": false, "error": "querying is not supported for dbms 'vectorai'"}` and `transaction()` raises. Do not use it here.

An extension that needs engine data calls the engine's REST API with its own HTTP client; `httpx` is installed in the image. Put the engine URL in the extension's `config` block. When the engine requires an API key, read it from an environment variable: the server does not hand its own key to extensions.

```python
import os
import httpx

client = None

async def setup(config):
    global client
    headers = {}
    if os.environ.get("MY_EXT_API_KEY"):
        headers["api-key"] = os.environ["MY_EXT_API_KEY"]
    client = httpx.AsyncClient(base_url=config["engine_url"], headers=headers, timeout=30)

async def teardown():
    await client.aclose()

def register(server, config):
    @server.tool(name="engine_count")
    async def engine_count(collection: str) -> dict:
        r = await client.post(f"/collections/{collection}/points/count", json={})
        r.raise_for_status()
        return r.json()
```

Every request runs with that key, whoever the caller is. The key decides what the extension can read or write, and nothing limits it to the collections listed in `conf.json`: that limit lives in the built-in tools, not in the engine.

## Requesting Write Approval {#asking-a-human-to-approve-a-write}

Nothing confirms an extension's write automatically. Call `request_write_confirmation()` and write only if it returns `True`. That lets you confirm once for a batch, add context, or skip confirmation in a trusted automated flow.

```python
from actian_mcp_server.extension_api import request_write_confirmation

async def drop_points(collection: str, ids: list) -> dict:
    approved = await request_write_confirmation(
        description=f"Delete {len(ids)} points from {collection}",
        details={"collection": collection, "ids": ids},
    )
    if not approved:
        return {"success": False, "error": "Write rejected by user"}

    r = await client.post(f"/collections/{collection}/points/delete",
                          json={"points": ids}, params={"wait": "true"})
    r.raise_for_status()
    return {"success": True, "deleted": len(ids)}
```

It returns `True` only on explicit approval. A decline, a timeout, or a client that cannot show the prompt all return `False`, so "proceed only if `True`" is safe. It also works for any other action that changes something, such as a call to an external API.

## Extension Security Controls

### Write Scope Enforcement

The automatic `mcp:write` check sits in the SQL transaction, so on a VectorAI DB server it never runs for an extension. When OAuth is on, check the scope yourself before a write:

```python
from actian_mcp_server.extension_api import has_scope

if not has_scope("mcp:write"):
    return {"success": False, "error": "write operations require the 'mcp:write' scope"}
```

`has_scope()` and `get_current_scopes()` return values only in read-write mode with OAuth enabled. Without OAuth every scope reads as absent, so do not make the check unconditional. Grant `mcp:write` to the users allowed to write, as described for [Auth0](../authentication/auth0.md) and [Keycloak](../authentication/keycloak.md).

### Execution Identity

Every engine request an extension makes runs with the key the extension sends, whoever the caller is. `get_current_user()` still names the caller, so an extension can log who asked, and `request_write_confirmation()` asks them before a write.

### Confirmation Prompt Behavior

The `write_confirmation` setting does not silence the extension's prompt. If your extension calls `request_write_confirmation()`, the prompt always appears. The `write_confirmation` setting in `conf.json` applies only to the server's built-in write tools. This works both ways:

- You cannot use that setting to skip an approval step your extension asked for.
- Turning it on for a client that cannot display prompts does not silently approve your extension's writes. The server rejects those writes and nothing is written.

## Rules and Caveats

!!! warning "A bad extension stops the server from starting"
    This behavior is deliberate. A misconfigured extension never leaves the server running in a quietly degraded state with fewer tools than you configured. Startup aborts if a module cannot be imported, does not define `register()`, raises during `register()`, or registers a tool whose name matches a built-in tool or an earlier extension. Any tools that extension already registered are rolled back first.

| Point | Detail |
|-------|--------|
| Tool names | Pick distinct, descriptive names. A collision with a built-in name such as `search` aborts startup. |
| No hot reload | Extensions load at startup. Restart the server to pick up changes. |

!!! important "Trust model"
    Extensions run in the same process with full Python access. Load only extensions you trust, the same way you would treat installing a Python package. Hiding the connection details is encapsulation, not a sandbox.

## Next Steps

<div class="grid cards" markdown>

- :material-file-code: **[Examples](examples.md)**  
  Five runnable extensions written for the SQL plugins; use them as templates for `register()`, tools, resources and the approval prompt.

- :material-book-open-variant: **[API reference](api-reference.md)**  
  Every function, signature, and return shape.

- :material-database-edit: **[Write support](../write-support.md)**  
  How `query_mode` and the write authorization gates work.

</div>
