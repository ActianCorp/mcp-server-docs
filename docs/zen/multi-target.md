---
title: Multiple Databases
description: Serve several Zen databases and personas from one Actian MCP Server container, each at its own URL, with read-only personas, per-target scopes, and hot add and remove through targets.d.
---

# Serving Multiple Databases from One Server

Without a `targets` block, one container serves one database at one URL, `/mcp`. With a `targets` block, the same container serves a list of entries — engine, persona, database — each at its own URL and each with its own connection to Zen. Nothing else changes: same image, same `docker run` command, one more block in `conf.json`.

## How an Entry Becomes a URL

```text
{"host": "zen16", "instance": "admin", "databases": ["DEMODATA"]}
          |                   |                      |
          v                   v                      v
http://<mcp-host>:8000/mcp/zen16/admin/DEMODATA/mcp
                       ^^^^^ ^^^^^ ^^^^^^^^
                      engine persona database
```

| Part | Meaning |
|------|---------|
| `host` | The Zen engine as the container reaches it — the same value you would put after `ServerName=` in a connection string. It is also the first URL segment. |
| `instance` | A persona label. Zen has no installation code, so this is a word you choose; it never reaches the engine and only names the URL. |
| `databases` | One or more Zen database names (`DBQ`). Each becomes a URL. |

The first `mcp` in the path is the configurable prefix (`target_path_prefix`, default `mcp`); the last `mcp` is the endpoint. The `list_accessible_targets` tool returns the path of every entry the caller may use, see [Tools](tools/index.md#list_accessible_targets).

## Configuration

Three entries: a read-only persona and an admin persona on `DEMODATA`, and an application persona on `DEFAULTDB`, all on the engine `zen16`.

```json
{
  "database": "DEMODATA",
  "conn_string": "Driver=/opt/actianzen/lib64/libodbcci.so;ServerName=zen16:1583;DBQ=DEMODATA",
  "query_mode": "read-write",
  "host": "0.0.0.0",
  "port": 8000,
  "allow_unscoped_reads": true,
  "zen_readonly_personas": ["readonly"],
  "targets": {
    "defaults": {
      "driver": "/opt/actianzen/lib64/libodbcci.so",
      "port": 1583,
      "max_connections": 4,
      "username": "Master",
      "password": "x"
    },
    "list": [
      {"host": "zen16", "instance": "readonly", "databases": ["DEMODATA"]},
      {"host": "zen16", "instance": "admin",    "databases": ["DEMODATA"]},
      {"host": "zen16", "instance": "app",      "databases": ["DEFAULTDB"]}
    ]
  }
}
```

| URL | Connects to | Writes |
|-----|-------------|--------|
| `/mcp/zen16/readonly/DEMODATA/mcp` | zen16, DEMODATA | refused by the engine (read-only persona) |
| `/mcp/zen16/admin/DEMODATA/mcp` | zen16, DEMODATA | allowed (server is `read-write`) |
| `/mcp/zen16/app/DEFAULTDB/mcp` | zen16, DEFAULTDB | allowed |
| `/mcp` | nothing | every tool answers "no target bound to this URL" |

### Configuration Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `targets.defaults` | `object` | — | Values shared by every entry. `driver` and `port` as in the connection string (`port` defaults to `1583`). `username` and `password` must be non-empty — Zen ignores them when database security is off, so a placeholder is fine. `max_connections` is required by the framework and not applied to Zen, see [Limits](#limits). |
| `targets.list` | `array` | — | One object per engine and persona. `host`, `instance` and `databases` are mandatory; any key from `defaults` may be repeated to override it for that entry, for example a `username` and `password` for an engine with Zen security on. |
| `zen_readonly_personas` | `array` | `[]` | Persona labels whose connections are opened read-only. See [Read-only personas](#read-only-personas). |
| `allow_unscoped_reads` | `boolean` | `false` | Lets a caller without a per-target grant read. Required to run more than one target **without** authentication; with authentication it disables per-target enforcement and is for test setups only. See [Authentication](authentication/index.md#per-target-scopes). |
| `targets_dir` | `string` | `/app/targets.d` | Directory of additional target files, see [Adding a database without a restart](#adding-a-database-without-a-restart). The directory must exist when the server starts. |
| `targets_reload_interval` | `integer` | `10` | Seconds between checks of `targets_dir`. `0` loads the directory once at start and never again. |
| `target_path_prefix` | `string` | `mcp` | First segment of every routed URL. |

!!! note "`conn_string` stays required"
    The server still opens the connection described by `conn_string` (or `database`) at start, as it did before. The targets add their own connections on top. Point it at any database the engine has.

!!! note "More than one target needs authentication or the escape hatch"
    Several targets without an identity provider and without `allow_unscoped_reads: true` stop the server at start: `N targets are configured, but per-target scope enforcement ... is not active`. With the hatch, anyone who can reach a URL may use it, exactly as a single-database server without OAuth. For a deployment with real users, configure [resource-server mode](authentication/index.md#resource-server-mode) and leave `allow_unscoped_reads` out.

## Read-only Personas

A persona listed in `zen_readonly_personas` is opened read-only even when `query_mode` is `read-write`: every connection of that target carries the ODBC attribute `SQL_ATTR_ACCESS_MODE=READ_ONLY` and `OPENMODE=1` in its connection string, and the engine refuses every write with `Access denied to a READ-ONLY data source`. The word `readonly` is not special — `zen_readonly_personas: ["analyst"]` with `"instance": "analyst"` works the same.

What a read-only persona does not do:

- It does not hide the write tools. Under multi-target the server publishes one tool list for all URLs, so `execute_write_query` is listed on the read-only URL as well; the engine refuses it.
- It does not give rights finer than read or write. For that, use Zen logins: with Zen security on, give each entry its own `username` and `password`, and the engine enforces that user's permissions. A `SELECT` on a table the login may not see fails with a Zen permission error.

## Adding a Database Without a Restart

Mount a directory at `/app/targets.d` when you start the container (`-v /path/to/targets.d:/app/targets.d`). Its presence switches the feature on. Later, drop a file into it:

```json title="targets.d/hr.json"
{"host": "zen16", "instance": "hr", "databases": ["DEFAULTDB"]}
```

Within `targets_reload_interval` seconds the URL `/mcp/zen16/hr/DEFAULTDB/mcp` answers. Delete the file and the URL returns `404` and its connection to Zen closes. A file may hold one entry or a JSON list of entries; `targets.defaults` applies to them too. A file that is not valid JSON is reported in the log and the registry keeps its previous contents.

## What the Agent Sees

- Each URL has its own instructions text (the mode, and a summary of the tables of that database) and its own `resource://database/schema` content. An agent connected to `app/DEFAULTDB` is told about DEFAULTDB, not about DEMODATA.
- `list_accessible_targets` returns every entry with its `path`, and a full `url` when `FASTMCP_SERVER_AUTH_BASE_URL` is configured. With authentication on, the list contains only the targets the caller's token grants.
- No switching databases inside one session: `database_manage` with `action=switch` is refused on a routed URL. To work with another database, connect to its URL.
- The [call log](index.md#call-log) carries the target of each call as `host/instance/database`, so calls through different URLs are told apart afterwards.

## Limits

- Zen keeps its single-database connection model per target: one connection set per entry, with one ODBC handle per worker thread. The framework's pool settings `max_connections`, `breaker_enabled` and `pool_idle_ttl` are accepted in the configuration but not applied to Zen.
- Several URLs on one database are several Zen sessions. `DROP TABLE` through `admin/DEMODATA` can fail with Zen status `-1304` while the `readonly` session has the table open, as with any two Zen clients today.
- Zen never sees the person behind the agent: every URL connects as the login in its entry. With authentication on, the token's user name goes to the call log, see [Authentication](authentication/index.md#resource-server-mode).

## Verifying a Setup

1. Connect an agent to each URL and call `list_tables`; the lists must differ between databases.
2. On the read-only URL ask for an `INSERT`; expect `Access denied to a READ-ONLY data source`.
3. On the admin URL run the same `INSERT`; expect the approval prompt, then success.
4. Read `resource://database/schema` on two URLs; the content must follow the URL.
5. Call a tool on the plain `/mcp` URL; expect "no target bound".
6. Drop a file into `targets.d`; the new URL must answer without a restart. Remove it; the URL must return `404`.

## Next Steps

<div class="grid cards" markdown>

- :material-lock: **[Authentication](authentication/index.md#resource-server-mode)**
  Give each URL its own read and write grants with tokens from your identity provider.

- :material-server-network: **[Deployment Scenarios](deployment.md)**
  Where the engine, the server and the agents sit, and which settings each layout needs.

- :material-tools: **[Tools](tools/index.md#list_accessible_targets)**
  How an agent discovers the URLs it may use.

</div>
