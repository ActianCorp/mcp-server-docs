---
title: Changing Targets Without a Restart
description: How to add, change, and remove a target of the Actian MCP Server for NoSQL without a restart by keeping one file per target in a directory the server reads again.
---

# Changing Targets Without a Restart

Targets that come from a directory are added, changed, and removed while the server runs. You keep one file per target in a directory, and the server reads the directory again at a fixed interval. The `nsql.targets[i]` entries and `nsql.connectionURL` are not reloaded, and a restart applies a change to them.

## Targets Directory

| Property | Default | Description |
|----------|---------|-------------|
| `nsql.targets.dir` | None | A directory of `*.properties` files, one target per file. Setting it alone is enough to run with targets. It combines with `nsql.targets[i]` but not with `nsql.connectionURL`. The environment form is `NSQL_TARGETS_DIR`. |
| `nsql.targets.reload-interval` | `10s` | How often the directory is read again. `0` reads it once at startup and never again. Otherwise the value is at least `1s` and at most 365 days. It is checked at every startup, also when `nsql.targets.dir` is not set. The environment form is `NSQL_TARGETS_RELOAD_INTERVAL`. |

```properties
nsql.targets.dir=/etc/nsql-mcp/targets.d
nsql.targets.reload-interval=10s
```

A directory with no files is allowed. The server starts, plain `/mcp` and `list_accessible_targets` work, and every `/mcp/<name>` answers as a name that was never configured until a file is added.

A poll does not start while the previous one is still running.

## File Format

A file holds the two keys `name` and `connectionURL`, each exactly once, and no other key. Keys are case-sensitive. The name and the connection URL follow the rules in [Target Names and Connection URLs](index.md#target-names-and-connection-urls), the same as for an `nsql.targets[i]` entry. An example file `/etc/nsql-mcp/targets.d/hr.properties`:

```properties
name=hr
connectionURL=hr_db@hr-db.example.com:5019#<USER>:<PASSWORD>
```

- A file is in the standard Java properties format, read as UTF-8, and may hold blank lines and comment lines.
- A file is at most 16 KiB, and the directory holds at most 1000 files.
- Only regular files directly in the directory count, and only when the name ends in `.properties` and does not start with `.`. Subfolders are ignored, and symbolic links are followed.
- The file name does not matter. The target is named by the `name` key.

## Credentials in the Directory

The password is written in the file as it is. A `${...}` reference is not expanded in a directory file, and a `$` stays a plain `$`. A backslash anywhere in a file other than a comment line is refused, so write the connection URL without one.

The directory therefore holds credentials. Use a directory that only the server's user can read, and do not place it in a world-readable location or in an image. On Kubernetes, keep the files in a Secret mounted as a directory, never with `subPath`: Kubernetes does not update a `subPath` mount, so the server would never see a change.

## Replacing a File

Write the new content to a file name that starts with `.`, which the server ignores, and then rename that file over the old one. The server then never reads a half-written file.

## How Changes Are Applied

- Every poll reads every file, builds the complete new set of targets, and checks it as a whole: each file, and across files a duplicate name, a name that is also in `nsql.targets[i]`, and the same database twice.
- The new set is applied all or nothing. A set that fails a check leaves the running set exactly as it was, and the server logs the problem once, naming the file and the rule and never a value.
- One bad file holds back every pending change until it is fixed. Once it is fixed, all pending changes apply together.
- A bad file at startup stops startup. So does a directory that does not exist, cannot be read, or is set to an empty value. After startup, a directory that cannot be read leaves the running targets as they are, and the next poll tries again.
- Each instance of the MCP server reads its own copy of the directory. See [Several Instances and Directory Changes](../limits.md#several-instances-and-directory-changes).

## What Each Change Does

| Change | What happens | What clients see |
|--------|--------------|------------------|
| A file is added | The target is added. | `/mcp/<name>` answers, and `list_accessible_targets` lists the target, from the next poll that applies. The tool lists at other endpoints do not change. |
| Only the user or password in `connectionURL` changes | The target keeps its database. New calls use the new login. Calls running and cursors open keep the old login, and the old connection pool closes once its last call and cursor end. | Nothing is interrupted. A cursor keeps paging even when the new password is wrong, and only new calls need the new login. Pending write confirmations of stateless clients and stateful sessions stay valid. |
| The host, port, or database changes | The target is removed and added again. | An open cursor from before the change is refused, and the client runs its query again. Pending write confirmations are refused, and the client starts over. A stateful session opened before the change is refused, and the client connects again. A call already running on the old database finishes. |
| The `name` key changes | The old name is removed and the new name is added. | The old name answers like a name that was never configured. The new name behaves like an added file. |
| A file is renamed and its content stays | Nothing. A target is identified by its `name` key, not by its file name. | Nothing. |
| A file is deleted | The target is removed. Calls running finish. Open cursors close, and the connection pool closes, once the last running call ends. Pending confirmations and session pins of the target are dropped. | A new request at the name is answered like a name that was never configured: `404` with authentication off, and the `403` [scope challenge](../authentication/scopes.md#what-a-caller-gets) with authentication on. This includes a cursor page, a confirmation retry, and a stateful session on that name. |
| A removed name is added again | A new target is created. It honours no cursor, confirmation, or session of the old one. | The same as an added file. |

Directory targets are reached with the same scopes as `nsql.targets[i]` targets. An extension limited to a target by name is offered there as soon as a target of that name exists. See [Limiting an Extension to Some Targets](../extensions/index.md#limiting-an-extension-to-some-targets).

## Next Steps

<div class="grid cards" markdown>

- :material-database: **[Targets](index.md)**  
  Targets, names, and what an agent sees.

- :material-lock: **[Authentication](../authentication/index.md)**  
  Secure the server with OAuth 2.0 and an external identity provider.

</div>
