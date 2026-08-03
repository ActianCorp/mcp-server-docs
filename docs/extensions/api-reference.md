---
title: API Reference
description: Every function, signature, and return shape available to an Actian MCP Server extension.
---

# API reference

Everything an extension needs is importable from `actian_mcp_server.extension_api`. The public functions are `get_current_user`, `get_current_scopes`, `has_scope`, `get_database`, and `request_write_confirmation`. The database and transaction objects come from `get_database()` rather than being imported.

## Module entry points

You define these in your module. See [Write the module](index.md#write-the-module).

| Symbol | Signature | Notes |
|--------|-----------|-------|
| `register` | `register(server, config) -> None` | Required, synchronous. Called once at startup. Register tools, resources, and prompts on `server`. `config` is your scoped settings. |
| `setup` | `setup(config)` | Optional. Open resources at startup. May be `async` or plain. |
| `teardown` | `teardown()` | Optional. Release resources at shutdown, in reverse load order. May be `async` or plain. |

## Functions

You call these.

| Symbol | Signature | Returns |
|--------|-----------|---------|
| `get_current_user` | `get_current_user() -> str \| None` | The authenticated username, or `None` when OAuth or impersonation is off. Treat `None` as unknown, not as an authorization decision. |
| `get_current_scopes` | `get_current_scopes() -> frozenset[str]` | The scopes on the current request's access token, as exact strings. Empty unless OAuth is enabled and the server is in read-write mode. |
| `has_scope` | `has_scope(scope: str) -> bool` | `True` if the current token carries `scope`, matched exactly. Same availability as `get_current_scopes()`. For your own checks. The `mcp:write` gate is enforced for you. |
| `get_database` | `get_database() -> DatabaseAccess` | The database facade. |
| `request_write_confirmation` | `await request_write_confirmation(description: str, details: dict \| None = None, timeout: int = 60) -> bool` | `True` only on explicit approval. A decline, cancel, timeout, or missing context returns `False`. `description` and `details` are shown to the user. |

## DatabaseAccess

Returned by `get_database()`.

| Method | Signature | Behavior |
|--------|-----------|----------|
| `query` | `await db.query(sql: str, params=None) -> dict` | Runs one `SELECT`. Non-`SELECT` statements are refused. Returns a result dictionary. Works in read-only mode. |
| `transaction` | `db.transaction(timeout: int = 300) -> Transaction` | Returns a transaction that has not started yet, the only way to write. `timeout` is the stale-transaction watchdog in seconds. Requires read-write mode. |

There is no `db.write()`. Every write goes through a transaction. Bind `params` as a list against `?` placeholders, and always parameterize user input.

## Transaction

Returned by `db.transaction()`.

| Member | Signature | Behavior |
|--------|-----------|----------|
| Context manager | `async with db.transaction() as tx:` | Commits on a clean exit, rolls back on an exception, and always releases the connection. |
| `begin` | `await tx.begin() -> Transaction` | Starts the transaction explicitly. The context manager calls this for you. Raises if the server is not in read-write mode, if the caller's token lacks `mcp:write`, or if the authenticated user cannot be resolved when impersonation is required. |
| `query` | `await tx.query(sql, params=None) -> dict` | A `SELECT` on the pinned connection. Sees the transaction's own uncommitted writes. Raises on failure. |
| `write` | `await tx.write(sql, params=None) -> dict` | Data Manipulation Language (DML) on the pinned connection. Raises on failure, aborting the transaction. |
| `commit` | `await tx.commit() -> dict` | Commits and releases. Raises if the commit fails or the transaction already finished. |
| `rollback` | `await tx.rollback() -> dict` | Rolls back and releases. |

!!! note "Failures behave differently inside a transaction"
    `db.query()` returns `{"success": false, ...}` on failure, while a transaction's `query()` and `write()` raise. That is what makes a failed statement abort the whole transaction.

## Result dictionary

`db.query()` and a successful `tx.query()` or `tx.write()` return:

```python
{
    "success": True,
    "columns": ["col", ...],
    "rows": [[...], ...],
    "row_count": 5,
}
```

Reads may also include `"truncated": True` and a `"warning"` when the result exceeded `max_rows`. For `tx.write()`, `columns` and `rows` are empty and `row_count` is the number of rows affected.

On failure, `db.query()` returns the following. A transaction's statements raise instead.

```python
{
    "success": False,
    "error": "<message>",
}
```
