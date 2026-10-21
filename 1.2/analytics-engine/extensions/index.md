---
title: Extensions
description: Add your own tools, resources, and prompts to the Actian MCP Server by writing a Python extension module.
---

# Extensions

You can extend the Actian MCP Server with **extensions**: your own Python modules that register extra tools, resources, and prompts on the running server, next to the built-in database tools. Use this for business logic you want an AI agent to call through the same endpoint, such as revenue forecasting, compliance checks, or data enrichment.

An extension *adds* capabilities. It does not manage the database connection. The server is already connected to your database and already exposes the built-in tools. The module provides a `register()` function and reads or writes through the extension API.

Extensions are supported on Actian Analytics Engine.

## Writing the Module

An extension is a normal Python module exposing one required function and two optional hooks:

```python
from actian_mcp_server.extension_api import (
    get_current_user,            # authenticated identity, or None
    get_database,                # .query() to read, .transaction() to write
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
    The `config` argument holds the `config` block you set in `conf.json` plus a short list of non-secret values (`dbms`, `max_rows`, `transport`). It never contains the database password, the connection string, or OAuth secrets.

Give your tools schema-friendly signatures: typed parameters, and no `*args` or `**kwargs`.

## Mounting and Registering the Module

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

## Reading Data

Reach the database only through `get_database()`. You never receive a connection, pool, cursor, or credentials.

```python
from actian_mcp_server.extension_api import get_database

db = get_database()
result = await db.query("SELECT * FROM orders WHERE id = ?", [order_id])
if result["success"]:
    for row in result["rows"]:
        ...
```

Always bind user input to `?` placeholders rather than building SQL strings.

`query()` runs one read, works in read-only mode, and behaves the same on every supported database. It is asynchronous, so `await` it. For table and column metadata, select from the engine's system catalogs.

## Writing Data

There is no one-shot write. Every write goes through a transaction opened with `get_database().transaction()`. A single write is a one-statement transaction, and several statements run all or nothing. A transaction pins one connection for its lifetime.

Set `"query_mode": "read-write"` in `conf.json` to allow writes. The default is `read-only`, and in that mode starting a transaction raises and nothing is written. See [Write support](../write-support.md).

The recommended form is the asynchronous context manager. It commits on a clean exit, rolls back if anything raises, and always releases the connection:

```python
from actian_mcp_server.extension_api import get_database

async def record_sale(customer_id: int, amount: float) -> dict:
    async with get_database().transaction() as tx:
        await tx.write("INSERT INTO orders (customer_id, amount) VALUES (?, ?)",
                       [customer_id, amount])
        await tx.write("UPDATE customer_revenue SET total_revenue = total_revenue + ? "
                       "WHERE customer_id = ?", [amount, customer_id])
        rows = await tx.query(
            "SELECT total_revenue FROM customer_revenue WHERE customer_id = ?",
            [customer_id])          # reads see the uncommitted changes
    # reached only if both writes succeeded and the transaction committed
    return {"success": True, "new_total": rows["rows"][0][0]}
```

You can also drive it explicitly when you need step-by-step control:

```python
tx = await get_database().transaction().begin()
try:
    await tx.write(...)
    await tx.commit()
except Exception:
    await tx.rollback()
    raise
```

### Choosing Between Query and a Transaction

| Need | Use |
|------|-----|
| A single read | `get_database().query()`. Lighter, and the only option on a read-only server. |
| A read that must see your own in-progress writes | `tx.query()` inside the transaction. |
| Any write, one statement or many | `get_database().transaction()` with `tx.write()`. |

Do not open a transaction only to read.

!!! warning "Statements raise inside a transaction"
    `db.query()` returns `{"success": false, ...}` on failure, but a transaction's `query()` and `write()` **raise**. That is deliberate: a failed statement aborts the whole transaction. Under `async with` it rolls back for you.

`tx.write()` runs `INSERT`, `UPDATE`, and `DELETE`. Data Definition Language (DDL) and administrative statements such as `SET` are refused, as they are for reads. A transaction left neither committed nor rolled back is rolled back by a watchdog, five minutes by default, so the connection cannot leak. Prefer `async with`, which releases promptly.

### Asking a Human to Approve a Write

Writes are not confirmed automatically. You decide where approval belongs: call `request_write_confirmation()` and write only if it returns `True`. That lets you confirm once for a batch, attach additional context, or skip confirmation in a trusted automated flow.

```python
from actian_mcp_server.extension_api import get_database, request_write_confirmation

async def tag_vip(customer_id: int) -> dict:
    approved = await request_write_confirmation(
        description=f"Tag customer {customer_id} as VIP",
        details={"table": "customers", "customer_id": customer_id},
    )
    if not approved:
        return {"success": False, "error": "Write rejected by user"}

    async with get_database().transaction() as tx:
        await tx.write("UPDATE customers SET vip = 1 WHERE customer_id = ?", [customer_id])
    return {"success": True}
```

It returns `True` only on explicit approval. A decline, a timeout, or a client that cannot show the prompt all return `False`, so "proceed only if `True`" is safe. You can also use it to gate a non-SQL action, such as an external API call that changes something.

## Extension Security Controls

An extension does not run with the server's own privileges. Three controls apply whether or not you write any code for them.

### Write Scope Enforcement

The write scope is enforced automatically. When OAuth is enabled, starting a transaction requires the caller's access token to carry the `mcp:write` scope. Without it the transaction raises and nothing is written. Reads need no extra scope. No action is required to enable this behavior. Grant `mcp:write` to the users or roles allowed to write, as described for [Auth0](../authentication/auth0.md) and [Keycloak](../authentication/keycloak.md).

For finer-grained checks, read the token's scopes with `has_scope()` or `get_current_scopes()`. Both return values only in read-write mode.

### End-User Execution

Statements run as the end user. On Analytics Engine, your statements run as the authenticated user, not as the server's service account.

!!! warning "Your extension is bounded by the user's own privileges"
    Because statements run as the end user, that user needs the table privileges your extension relies on, and your extension cannot read or write anything the user could not reach directly. When impersonation is required but the user cannot be resolved, the transaction is **rejected** rather than falling back to the service account.

### Confirmation Prompt Behavior

The `write_confirmation` setting does not silence the extension's prompt. If your extension calls `request_write_confirmation()`, the prompt always appears. The `write_confirmation` setting in `conf.json` applies only to the server's built-in write tools. This works both ways:

- You cannot use that setting to skip an approval step your extension asked for.
- Turning it on for a client that cannot display prompts does not silently approve your extension's writes. The server rejects those writes and nothing is written.

## Rules and Caveats

!!! warning "A bad extension stops the server from starting"
    This behavior is deliberate. A misconfigured extension never leaves the server running in a quietly degraded state with fewer tools than you configured. Startup aborts if a module cannot be imported, does not define `register()`, raises during `register()`, or registers a tool whose name matches a built-in tool or an earlier extension. Any tools that extension already registered are rolled back first.

| Point | Detail |
|-------|--------|
| Tool names | Pick distinct, descriptive names. A collision with a built-in name such as `execute_query` aborts startup. |
| No hot reload | Extensions load at startup. Restart the server to pick up changes. |

!!! important "Trust model"
    Extensions run in the same process with full Python access. Load only extensions you trust, the same way you would treat installing a Python package. Hiding the connection details is encapsulation, not a sandbox.

## Next Steps

<div class="grid cards" markdown>

- :material-file-code: **[Examples](examples.md)**  
  Five runnable extensions, with configuration and schema files.

- :material-book-open-variant: **[API reference](api-reference.md)**  
  Every function, signature, and return shape.

- :material-database-edit: **[Write support](../write-support.md)**  
  How `query_mode` and the write authorization gates work.

</div>
