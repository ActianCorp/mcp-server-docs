---
title: Health Tools
description: Built-in, read-only tools that report the operational health of an Actian Ingres installation and database, with thresholds you can tune in conf.json.
---

# Health Tools

The Actian MCP Server for Actian Ingres includes seven built-in tools that report the operational health of the Ingres installation and of the connected database. An MCP client or AI assistant can use them to answer questions such as "when did this database last checkpoint?", "is anything holding locks?", or "is the optimizer planning against stale statistics?" without you writing catalog queries by hand.

The tools read the Ingres Management Architecture database (`imadb`) and the connected database's own system catalogs. They are available only on Actian Ingres. The Actian Analytics Engine server does not provide them.

!!! note "Read-only"
    Every health tool only reads. No health tool changes database state, takes a checkpoint, runs `optimizedb`, or ends a session. Remediation remains a task for Ingres tooling or for an approved write. All seven tools are advertised to clients as read-only. See [Tool annotations](tools/index.md#tool-annotations).

## Available Tools

| Tool | Question it answers | Scope |
|------|---------------------|-------|
| [`server_status`](#server_status) | Can the server reach my database, and what is the state of the Ingres server? | Installation (reachability verdict is for the database) |
| [`checkpoint_journal_health`](#checkpoint_journal_health) | When was the last checkpoint, and is every user table journaled? | Database |
| [`locking_health`](#locking_health) | How much lock capacity is in use, and how many deadlocks and lock waits have occurred? | Installation |
| [`long_running_queries`](#long_running_queries) | Which queries are running right now, and for how long? | Database |
| [`cache_io_health`](#cache_io_health) | How is the buffer cache performing, and is the log writer keeping up? | Installation |
| [`storage_health`](#storage_health) | Which tables have the most overflow or over-allocated pages? | Database |
| [`optimizer_health`](#optimizer_health) | Is the optimizer planning against current statistics? | Database |

None of the tools takes input parameters.

### Installation and Database Scope

An Ingres installation shares its lock table, buffer cache, log writer, and server processes across all of its databases. The health tools therefore report at one of two levels, stated in the `scope` field of every result:

| Scope | Meaning |
|-------|---------|
| `installation` | The answer describes the whole Ingres installation and is the same regardless of which database the server is connected to. |
| `database` | The answer describes only the database the server is connected to. Installation-wide data is filtered to that database, so the result never reports on other databases in the installation. |

## Reading a Result

Every health tool returns the same JSON envelope.

| Field | Type | Description |
|-------|------|-------------|
| `success` | `boolean` | `true` whenever the tool ran. A tool that could read only part of its data still returns `true` and lists the missing parts in `unavailable`. |
| `tool` | `string` | Name of the tool that produced the result. |
| `scope` | `string` | `installation` or `database`. See [Installation and database scope](#installation-and-database-scope). |
| `status` | `string` | Overall verdict for the call: the most severe status among the metrics. `server_status` and `long_running_queries` set it differently; see their sections. |
| `metrics` | `array` | One object for each reported value. See the following table. |
| `unavailable` | `array` | Parts of the read that failed. Always present; empty when everything was read. |
| `note` | `string` | A one-sentence finding, present only when a metric reached `warn` or `crit` or the tool has a finding of its own. A healthy result has no `note`. |
| `raw` | `object` | The catalog rows behind the metrics, each as `{"columns", "rows", "row_count"}`. Present when at least one block was read. |

Each entry in `metrics` carries its value together with the threshold that judged it, so a client can act on the result without looking anything up:

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Metric name. Per-database, per-session, and per-page-size metrics carry the qualifier in square brackets, for example `checkpoint_age_hours[sales]`. |
| `value` | number, string, or `null` | The measured value. `null` means the value could not be determined. |
| `unit` | `string` or `null` | Unit of a thresholded metric, such as `hours`, `tables`, `percent`, or `ratio`. `null` for informational metrics. |
| `status` | `string` | `ok`, `warn`, `crit`, or `info`. |
| `warn` | number or `null` | The warning threshold applied. `null` for informational metrics. |
| `crit` | number or `null` | The critical threshold applied. `null` when the metric has no critical level or is informational. |
| `note` | `string` or `null` | Context for the value, such as the table it refers to. |

### Status Values

| Status | Meaning |
|--------|---------|
| `ok` | The value is below the warning threshold. |
| `warn` | The value is at or above the `warn` threshold. |
| `crit` | The value is at or above the `crit` threshold. |
| `info` | Informational only. The value has no threshold, or it could not be measured. |

Thresholds are inclusive: a value equal to `warn` is reported as `warn`. The overall `status` ranks `crit` above `warn`, `warn` above `ok`, and `ok` above `info`, so a result whose metrics are all informational reports `info`.

Many values are reported as informational on purpose. Cumulative counters, such as deadlocks since server start, only ever increase, so a fixed threshold on them would always eventually warn. Capacity figures are reported as raw counts beside their limits rather than as percentages, so you can compare them against the definition you use.

### Partial Results

If part of a read fails, the tool still returns the parts it could read and adds an entry to `unavailable`:

| Field | Description |
|-------|-------------|
| `block` | The part of the read that failed, for example `db_config` or `lk_summary`. |
| `error` | The error the database returned. |
| `hint` | Likely causes. A missing privilege and a failed connection can produce the same error, so the hint names both rather than guessing. |
| `sqlstate` | The SQLSTATE code, when the error carries one. |

Check `unavailable` before treating a result as complete.

!!! note "A database Ingres is not holding open"
    Ingres lists a database in `imadb` only while it is open. If the connected database has not been opened since the Ingres server started, a database-scoped tool cannot read its installation-side data and reports this in `unavailable` rather than returning an empty, healthy-looking result. Any query against the database opens it, and the next health call reports its state.

## server_status

Reports whether the MCP server can reach the connected database, and summarizes the Ingres server.

The `status` field is a reachability verdict for the connected database, not the most severe metric:

| Status | Meaning |
|--------|---------|
| `ok` | The server opened a session to the connected database. |
| `crit` | The server could not reach the connected database. The error appears in `unavailable` under the block `database`, and `note` names the database. |

If this tool reports `crit`, the other health tools cannot answer for the database either. The installation facts are still reported, because a database can be unreachable while the installation is running.

The installation facts are all informational:

| Metric | Description |
|--------|-------------|
| `current_connections` | Live connections to the installation. |
| `highwater_connections` | Peak connections since the Ingres server started. |
| `server_state` | Operational state reported by the Ingres server. |
| `max_connections` | Configured connection limit of the Ingres server. Compare with `current_connections`. |
| `server_pid` | Process ID of the Ingres server. |
| `startup_time` | When the Ingres server started, in ISO 8601 UTC. |

### Example

The following result is illustrative.

```json
{
	"success": true,
	"tool": "server_status",
	"scope": "installation",
	"status": "ok",
	"metrics": [
		{"name": "current_connections", "value": 5, "unit": null, "status": "info", "warn": null, "crit": null, "note": "live connections to this installation"},
		{"name": "highwater_connections", "value": 7, "unit": null, "status": "info", "warn": null, "crit": null, "note": "peak connections since server start"},
		{"name": "server_state", "value": "OPERATIONAL", "unit": null, "status": "info", "warn": null, "crit": null, "note": "operational state reported by the server"},
		{"name": "max_connections", "value": 32, "unit": null, "status": "info", "warn": null, "crit": null, "note": "configured ceiling; compare with current_connections"},
		{"name": "server_pid", "value": 6289, "unit": null, "status": "info", "warn": null, "crit": null, "note": null},
		{"name": "startup_time", "value": "2026-10-05T22:05:50+00:00", "unit": null, "status": "info", "warn": null, "crit": null, "note": "server start, UTC; the catalog stores a zero-padded Unix epoch that is unreadable as published"}
	],
	"unavailable": [],
	"raw": {"server": {"columns": ["..."], "rows": [["..."]], "row_count": 1}, "server_parameters": {"columns": ["..."], "rows": [["..."]], "row_count": 1}}
}
```

## checkpoint_journal_health

Reports how recently the connected database was checkpointed and whether its user tables can be recovered from the journal.

**Scope:** database

| Metric | Threshold | Description |
|--------|-----------|-------------|
| `checkpoint_age_hours[<database>]` | `checkpoint_age_hours` | Hours since the most recent valid journal checkpoint, measured against the Ingres server's own clock. |
| `unjournaled_user_tables` | `unjournaled_user_tables` | Number of user tables that contain rows but are not journaled, and so cannot be rolled forward from the journal. |
| `journal_checkpoint_sequence[<database>]` | Informational | Journal checkpoint sequence number. This is a sequence, not a date. |
| `journal_ckp_count[<database>]` | Informational | Number of journal checkpoints. |
| `dmp_checkpoint_age_hours[<database>]` | Informational | Hours since the most recent valid dump checkpoint. |
| `log_writes[<database>]` | Informational | Log writes for the database. |
| `log_waits[<database>]` | Informational | Log waits for the database. |

If the Ingres server does not report its own time, the checkpoint ages are not calculated, an entry for `server_clock` appears in `unavailable`, and the checkpoint rows remain available in `raw`.

### Example

The following result is illustrative, shows only some of the metrics, and omits `raw`.

```json
{
	"success": true,
	"tool": "checkpoint_journal_health",
	"scope": "database",
	"status": "warn",
	"metrics": [
		{"name": "journal_checkpoint_sequence[sales]", "value": 5, "unit": null, "status": "info", "warn": null, "crit": null, "note": "monotonic sequence number, not a date"},
		{"name": "journal_ckp_count[sales]", "value": 5, "unit": null, "status": "info", "warn": null, "crit": null, "note": null},
		{"name": "checkpoint_age_hours[sales]", "value": 31.5, "unit": "hours", "status": "warn", "warn": 24, "crit": 72, "note": null},
		{"name": "unjournaled_user_tables", "value": 0, "unit": "tables", "status": "ok", "warn": 1, "crit": null, "note": "user tables with rows that cannot be rolled forward from the journal"}
	],
	"unavailable": [],
	"note": "checkpoint_age_hours[sales] = 31.5 hours (above 24/72)"
}
```

## locking_health

Reports lock capacity, live lock counts, and deadlock and lock-wait counters.

**Scope:** installation

All metrics are informational. Capacity figures are published as raw counts beside their limits, and the deadlock and wait figures are cumulative since the Ingres server started.

| Metric | Description |
|--------|-------------|
| `locks_inuse`, `locks_available`, `locks_remaining` | Locks in use, and lock capacity. |
| `lock_lists_available`, `lock_lists_remaining`, `lkd_llb_inuse` | Lock list capacity and use. |
| `lkd_max_lkb` | Maximum lock blocks. |
| `resources_inuse`, `resources_remaining` | Lock resources in use and remaining. |
| `lkd_stat_deadlock` | Deadlocks since server start. |
| `lkd_stat_wait`, `lkd_stat_convert_wait` | Lock waits and lock conversion waits since server start. |
| `lkd_stat_dlock_srch` | Deadlock searches since server start. |
| `lkd_stat_create_list` | Lock lists created since server start. |
| `live_locks`, `live_lock_lists` | Locks and lock lists held at the time of the call. |
| `log_transactions` | Open log transactions at the time of the call. |

### Example

The following result is illustrative, shows only some of the metrics, and omits `raw`.

```json
{
	"success": true,
	"tool": "locking_health",
	"scope": "installation",
	"status": "info",
	"metrics": [
		{"name": "locks_inuse", "value": 42, "unit": null, "status": "info", "warn": null, "crit": null, "note": "raw capacity; no ratio published in v1"},
		{"name": "locks_available", "value": 20000, "unit": null, "status": "info", "warn": null, "crit": null, "note": "raw capacity; no ratio published in v1"},
		{"name": "lkd_stat_deadlock", "value": 0, "unit": null, "status": "info", "warn": null, "crit": null, "note": "cumulative count since server start"},
		{"name": "live_locks", "value": 42, "unit": null, "status": "info", "warn": null, "crit": null, "note": null}
	],
	"unavailable": []
}
```

## long_running_queries

Reports the queries running in the connected database at the moment of the call, and how long each has been running.

**Scope:** database

| Metric | Description |
|--------|-------------|
| `active_sessions` | Number of sessions you can see that have a query in progress. `null` if the session read failed. |
| `query_elapsed_seconds[<session_id>]` | Whole seconds the session's current query has been running. The note gives the user, database, and session activity. |

The tool lists the 10 longest-running queries individually. `active_sessions` gives the total, so any sessions beyond the first 10 are counted rather than silently omitted. `raw.sessions` contains the same 10 rows, with the columns `session_id`, `effective_user`, `db_name`, `session_activity`, `server_pid`, and `elapsed_seconds`.

Consider the following when you read the result:

- **No threshold.** How long is too long depends on your workload, so all metrics are informational and a successful call reports `info`. The call reports `crit` only when the session read itself fails.
- **A snapshot, not a history.** A query that has already finished does not appear.
- **No statement text.** The SQL text can contain literal values, so the tool never returns it. To read a statement, take its `session_id` to `iimonitor`.
- **Some statements have no age.** Ingres records a start time for DML only. A statement without one, such as DDL, is still counted and listed, but its elapsed time is `null` and its note explains why.
- **Visibility depends on privilege.** The count reflects the sessions the querying user is permitted to see.

### Example

The following result is illustrative and omits `raw`.

```json
{
	"success": true,
	"tool": "long_running_queries",
	"scope": "database",
	"status": "info",
	"metrics": [
		{"name": "active_sessions", "value": 1, "unit": null, "status": "info", "warn": null, "crit": null, "note": "sessions visible to this caller with a query in progress; the 10 longest are listed individually"},
		{"name": "query_elapsed_seconds[<session_id>]", "value": 184, "unit": null, "status": "info", "warn": null, "crit": null, "note": "<database_user> on sales, (unknown)"}
	],
	"unavailable": []
}
```

## cache_io_health

Reports buffer cache activity and log writer pressure.

**Scope:** installation

All metrics are informational. Hit and read counts are published as raw cumulative counts; no hit ratio is calculated. Page sizes that have served no reads and no hits are omitted.

| Metric | Description |
|--------|-------------|
| `buffer_cache_hit_count[<page_size>]` | Cumulative buffer cache hits for the page size. |
| `buffer_cache_read_count[<page_size>]` | Cumulative buffer cache reads for the page size. Can be zero, so guard against division by zero if you form a ratio. |
| `buffer_cache_free_buffers[<page_size>]` | Free buffers for the page size. |
| `cache_wait_count`, `fc_flush_count`, `cache_lock_reclaims` | Buffer manager counters since server start. |
| `lgd_status` | Log writer status. |
| `logwriters` | Current number of log writers. |
| `max_log_writer_queue_length` | Highest log writer queue length. |
| `logwriter_waits` | Log writer waits since server start. |
| `logwriter_group_commits` | Log writer group commits since server start. |

`raw` also contains the query cache and query result cache statistics under `query_cache` and `qrc_cache`. These are not published as metrics.

### Example

The following result is illustrative, shows only some of the metrics, and omits `raw`.

```json
{
	"success": true,
	"tool": "cache_io_health",
	"scope": "installation",
	"status": "info",
	"metrics": [
		{"name": "buffer_cache_hit_count[8192]", "value": 1532044, "unit": null, "status": "info", "warn": null, "crit": null, "note": "raw cumulative count; ratio not published in v1"},
		{"name": "buffer_cache_read_count[8192]", "value": 74, "unit": null, "status": "info", "warn": null, "crit": null, "note": "raw cumulative count; guard against zero when forming a ratio"},
		{"name": "logwriters", "value": 1, "unit": null, "status": "info", "warn": null, "crit": null, "note": "current gauge, not a counter"}
	],
	"unavailable": []
}
```

## storage_health

Reports the user tables in the connected database with the most overflow pages and the most over-allocated space.

**Scope:** database

| Metric | Threshold | Description |
|--------|-----------|-------------|
| `table_overflow_pct` | `table_overflow_pct` | Overflow pages as a percentage of total pages, for the worst user table. The note names the table and its owner. |
| `extent_overalloc_ratio` | `extent_overalloc_ratio` | Allocated pages divided by the table's page count, for the worst user table. The note names the table and its owner. |
| `extent_locations` | Informational | Number of extent locations recorded for the database. |

Per-location disk space is not reported.

### Example

The following result is illustrative and omits `raw`.

```json
{
	"success": true,
	"tool": "storage_health",
	"scope": "database",
	"status": "warn",
	"metrics": [
		{"name": "table_overflow_pct", "value": 31.25, "unit": "percent", "status": "warn", "warn": 25, "crit": 50, "note": "worst table: order_lines (<table_owner>)"},
		{"name": "extent_overalloc_ratio", "value": 1.6, "unit": "ratio", "status": "ok", "warn": 4, "crit": 10, "note": "worst table: customers (<table_owner>)"},
		{"name": "extent_locations", "value": 1, "unit": null, "status": "info", "warn": null, "crit": null, "note": null}
	],
	"unavailable": [],
	"note": "table_overflow_pct = 31.25 percent (above 25/50)"
}
```

## optimizer_health

Reports whether the optimizer statistics in the connected database still describe the data.

**Scope:** database

The tool compares each table's current row count with the row count its statistics describe. The drift ratio is symmetric (the larger count divided by the smaller), so it flags a table that has grown and a table that has shrunk.

| Metric | Threshold | Description |
|--------|-----------|-------------|
| `stale_stats_drift_ratio` | `stale_stats_drift_ratio` | The largest drift ratio among user tables with statistics. The note names the table and its owner. |
| `statistics_tables` | Informational | Number of user tables with collected statistics. |
| `oldest_statistics_age_hours` | Informational | Age of the oldest collected statistics, in hours. |
| `no_statistics_tables` | Informational | Number of user tables with rows on which `optimizedb` has not collected statistics. |
| `histogram_segments` | Informational | Number of stored histogram segments. |

The tool distinguishes two answers that would otherwise look alike:

- If no statistics have been collected in the database, `note` says so and recommends running `optimizedb` to establish a baseline. This is not the same as "nothing is stale".
- A table that is empty on one side of the comparison but not the other has no finite drift ratio. Such tables are named in `note` instead of being reported as a number.

### Example

The following result is illustrative and omits `raw`.

```json
{
	"success": true,
	"tool": "optimizer_health",
	"scope": "database",
	"status": "warn",
	"metrics": [
		{"name": "histogram_segments", "value": 58, "unit": null, "status": "info", "warn": null, "crit": null, "note": "histogram rows, one per stored text segment"},
		{"name": "no_statistics_tables", "value": 2, "unit": null, "status": "info", "warn": null, "crit": null, "note": "user tables with rows that optimizedb has not collected on"},
		{"name": "statistics_tables", "value": 12, "unit": null, "status": "info", "warn": null, "crit": null, "note": "tables with collected statistics"},
		{"name": "oldest_statistics_age_hours", "value": 412.5, "unit": null, "status": "info", "warn": null, "crit": null, "note": "age of the oldest collected statistics"},
		{"name": "stale_stats_drift_ratio", "value": 3.4, "unit": "ratio", "status": "warn", "warn": 2.0, "crit": 5.0, "note": "worst table: orders (<table_owner>)"}
	],
	"unavailable": [],
	"note": "stale_stats_drift_ratio = 3.4 ratio (above 2.0/5.0)"
}
```

## Configuring Thresholds

The default thresholds suit most installations. To change them, add a `health` block to `conf.json`. Each threshold is an object with a required `warn` and an optional `crit`. You only need to list the thresholds you want to change; the others keep their defaults.

```json
{
  "health": {
    "checkpoint_age_hours":    { "warn": 24,  "crit": 72 },
    "unjournaled_user_tables": { "warn": 1,   "crit": null },
    "table_overflow_pct":      { "warn": 25,  "crit": 50 },
    "extent_overalloc_ratio":  { "warn": 4,   "crit": 10 },
    "stale_stats_drift_ratio": { "warn": 2.0, "crit": 5.0 },
    "query_timeout": 30
  }
}
```

The preceding example shows the defaults.

| Key | Unit | Default `warn` | Default `crit` | Used by | Meaning |
|-----|------|:--------------:|:--------------:|---------|---------|
| `checkpoint_age_hours` | hours | `24` | `72` | `checkpoint_journal_health` | Age of the most recent journal checkpoint. |
| `unjournaled_user_tables` | tables | `1` | none | `checkpoint_journal_health` | Number of user tables with rows that are not journaled. The default warns on the first such table and has no critical level. |
| `table_overflow_pct` | percent | `25` | `50` | `storage_health` | Overflow pages as a percentage of total pages, for the worst table. |
| `extent_overalloc_ratio` | ratio | `4` | `10` | `storage_health` | Allocated pages divided by the table's page count, for the worst table. |
| `stale_stats_drift_ratio` | ratio | `2.0` | `5.0` | `optimizer_health` | Divergence between a table's current row count and the row count its statistics describe, for the worst table. |

A metric reaches `warn` when its value is greater than or equal to `warn`, and `crit` when its value is greater than or equal to `crit`. Set `crit` to `null`, or leave it out, for a warning-only threshold.

### Query Timeout

`query_timeout` is not a threshold. It sets the maximum time, in seconds, that a single health query may run before it is abandoned.

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `query_timeout` | number | `30` | Maximum seconds for each health query. `0` means no limit. Must be zero or a positive number. |

The limit ensures that a health tool returns even when the Ingres server accepts connections but stops answering, which is often the situation in which you need the health tools most. A query that exceeds the limit is reported in `unavailable`.

### Validation

The server checks the `health` block at startup and does not start if the block cannot be applied as written. This prevents a mistyped key from silently leaving a threshold on its default. The server rejects:

- An unknown key, such as a misspelled metric name.
- A threshold that is not an object, or that has settings other than `warn` and `crit`.
- A threshold without `warn`.
- A `warn` or `crit` value that is not a number.
- A `crit` value that is not greater than `warn`, which would make the critical level unreachable.
- A `query_timeout` that is negative or not a number.

## Privileges and Connections

The health tools use the same database identity as the other tools. When [user impersonation](authentication/index.md) is active, each read runs as the authenticated user; otherwise it runs as the configured `database_user`. A health tool never reads with more privilege than the caller has through `execute_query`.

Each health call reads from two places:

- The installation's `imadb` database, for server, lock, cache, log, session, and checkpoint information. The server opens one separate connection to `imadb` for each health call and closes it when the call ends. This connection is not taken from the server's connection pool and counts toward the Ingres installation's connection limit while the call runs.
- The connected database's system catalogs, for table, journaling, page, and statistics information. These reads use the server's normal connection pool.

On the `imadb` connection, the server requests that reads take no read locks, so a health read does not block other sessions. If the Ingres server refuses that setting, the read still runs.

The identity used must be able to connect to `imadb` and to read the relevant Ingres catalogs. If it cannot, the affected parts appear in `unavailable` with the database error, and the tool still reports everything else. Catalog visibility can also be narrowed by privilege: for example, `long_running_queries` counts only the sessions the user is permitted to see.

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](tools/index.md)**  
  The query and catalog tools available for Actian Ingres.

- :material-database-cog: **[Ingres configuration](index.md#configuration-reference)**  
  The full `conf.json` reference for Actian Ingres.

- :material-lock: **[Authentication](authentication/index.md)**  
  Secure the server with OAuth 2.0 and configure user impersonation.

</div>
