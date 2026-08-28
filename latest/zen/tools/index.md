---
title: Tools
description: Built-in tools available when using the Actian MCP Server with Actian Zen.
---

# Tools

The Actian MCP Server for Actian Zen registers a different set of built-in tools per `query_mode` —
six in `read-only`, five in `read-write` — so the tool list a client discovers differs between the
two deployments. See [Write support](../write-support.md).

## Available Tools

| Tool | `read-only` | `read-write` | Description |
|------|:-----------:|:------------:|-------------|
| [`execute_query`](#execute_query) | ✓ | ✓ | Runs `SELECT` with automatic Zen dialect translation. Never writes in either mode. |
| [`list_tables`](#list_tables) | ✓ | ✓ | Lists all user tables from the Zen catalog. |
| [`describe_table`](#describe_table) | ✓ | ✓ | Returns column metadata, primary keys, and foreign keys for a table. |
| [`orm_operation`](#orm_operation) | ✓ select | ✓ select, insert, update, delete | Structured queries via SQLAlchemy with JOINs, WHERE, ORDER BY, GROUP BY, and LIMIT. |
| [`execute_write_query`](#execute_write_query) | — | ✓ | Runs a single `INSERT`, `UPDATE`, `DELETE`, or `MERGE`. |
| [`blob_operation`](#blob_operation) | ✓ | — | Lists and downloads file and blob data. |
| [`database_manage`](#database_manage) | ✓ | — | Queries server capabilities, lists DSNs, and releases locks. |

!!! note "Enabling write mode removes two tools"
    `blob_operation` and `database_manage` are registered in `read-only` mode only. A `read-write`
    server does not expose them, and they will not appear in the client's tool list. This is
    intentional.

Writes are authorized by the `mcp:write` scope and a human approval prompt, both described in
[Write support](../write-support.md). Data Definition Language, explicit transactions, and
bulk `batch_operation` are not available in any mode in this release.

---

## execute_query

Executes a read-only SQL query against Actian Zen with automatic dialect translation. It supports complex queries like JOINs, subqueries, aggregations, and UNION.

!!! warning "This tool never writes, even in read-write mode"
    Unlike the Ingres and Analytics Engine servers, where the same tool performs writes once
    `query_mode` is `read-write`, Zen accepts `SELECT` here in every mode. DML sent to
    `execute_query` is rejected with a pointer to the tool that performs the write:

    ```json
    {
      "error": "DML not allowed in execute_query. Use execute_write_query for INSERT/UPDATE/DELETE.",
      "alternative": "execute_write_query",
      "sql_classification": "DML"
    }
    ```

    Data Definition Language is rejected the same way, and is not enabled in any mode:

    ```json
    {
      "error": "DDL not allowed in this mode. Schema changes are blocked in 1.1 (deferred to full mode).",
      "sql_classification": "DDL"
    }
    ```

!!! note "Auto-translations"
    The following translations are applied automatically before execution:

    - `LEN()` → `CHAR_LENGTH()` (Zen does not support `LEN()`)
    - `INFORMATION_SCHEMA` queries → `dbo.fSQL*()` catalog functions
    - Constraint names are truncated to 20 characters (Zen limit)

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `sql` | `string` | ✓ | Read-only SQL query to execute. |

### Output Schema

**On Success**

```json
{
  "results": [{"column": "value"}],
  "row_count": 2,
  "method": "execute_query"
}
```

**When results are truncated**

Returned when the result set exceeds `max_rows` (default: `1000`).

```json
{
  "results": [{"column": "value"}],
  "row_count": 1000,
  "truncated": true,
  "truncation_note": "Results limited to 1000 rows. Use WHERE to narrow results.",
  "method": "execute_query"
}
```

**When dialect translation is applied**

```json
{
  "results": [],
  "row_count": 0,
  "translated": true,
  "translation_note": "Translated LEN() to CHAR_LENGTH() for Zen compatibility",
  "original_sql": "SELECT LEN(name) FROM customers",
  "method": "execute_query"
}
```

### Example

**Request**

```json
{
  "sql": "SELECT * FROM Person WHERE Last_Name LIKE 'S%' ORDER BY First_Name"
}
```

**Response**

```json
{
  "results": [
    {"ID": 101, "First_Name": "Alice", "Last_Name": "Smith"},
    {"ID": 102, "First_Name": "Bob", "Last_Name": "Sanders"}
  ],
  "row_count": 2,
  "method": "execute_query"
}
```

---

## list_tables

Returns all user tables in the connected database by querying the Zen `dbo.fSQLTables()` catalog function. System tables are excluded.

### Parameters

This tool takes no input parameters.

### Output Schema

**On Success**

```json
{
  "tables": ["<table_name>"],
  "count": "<num_tables>"
}
```

### Example

**Response**

```json
{
  "tables": ["Person", "Department", "Billing", "Student", "Class", "Tuition", "Faculty"],
  "count": 7
}
```

---

## describe_table

Returns column metadata for a table, including names, types, precision, scale, nullability, defaults, primary keys, and foreign keys. Internally uses the `dbo.fSQLColumns()`, `dbo.fSQLPrimaryKeys()`, and `dbo.fSQLForeignKeys()` catalog functions.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `table` | `string` | ✓ | Name of the table to describe. |

### Output Schema

**On Success**

```json
{
  "table_name": "<table_name>",
  "columns": [
    {
      "name": "<column_name>",
      "type": "<column_type>",
      "precision": "<precision>",
      "scale": "<scale>",
      "nullable": "<true|false>",
      "default": "<default_value>",
      "primary_key": "<true|false>"
    }
  ],
  "primary_keys": ["<primary_key_column>"],
  "foreign_keys": []
}
```

### Example

**Request**

```json
{
  "table": "Person"
}
```

**Response**

```json
{
  "table_name": "Person",
  "columns": [
    {
      "name": "ID",
      "type": "BIGIDENTITY",
      "precision": 19,
      "scale": 0,
      "nullable": false,
      "default": null,
      "primary_key": true
    }
  ],
  "primary_keys": ["ID"],
  "foreign_keys": []
}
```

---

## orm_operation

Performs structured queries via SQLAlchemy with dynamic model creation. Handles the Zen SQL dialect automatically.

Supports JOINs (up to 3 tables), WHERE conditions, ORDER BY, GROUP BY, HAVING, LIMIT, OFFSET, and aggregate functions (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`).

In `read-write` mode this tool also performs single-row writes. Those go through the same
`mcp:write` scope check and approval prompt as [`execute_write_query`](#execute_write_query).

### Parameters

**Required**

| Field | Type | Description |
|-------|------|-------------|
| `operation` | `string` | `select` in any mode. `insert`, `update`, and `delete` require `query_mode` set to `read-write`. |
| `table` | `string` | Target table name. |

**Optional**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `columns` | `list` | All columns | Columns to return. Supports aggregates like `COUNT(*) AS total`. |
| `where` | `dict` | — | Filter conditions, for example, `{"field": "salary", "operator": ">", "value": 50000}`. |
| `order_by` | `list` | — | Column names to sort by. |
| `limit` | `integer` | `max_rows` | Maximum rows to return. Capped at `max_rows`. |
| `offset` | `integer` | — | Number of rows to skip. |
| `joins` | `list` | — | Join specs: `[{"table": "dept", "on": "p.dept_id = dept.id", "type": "LEFT"}]`. |
| `group_by` | `list` | — | Columns to group by. |
| `having` | `dict` | — | HAVING conditions for grouped queries. |
| `data` | `dict` | — | Column values for `insert` and `update`. Requires `read-write`. |
| `entity_id` | `integer` | — | Primary-key value the `update` or `delete` targets. Requires `read-write`. |

### Output Schema

**On Success**

```json
{
  "results": [{"column": "value"}],
  "row_count": 2,
  "method": "orm_operation"
}
```

### Example

**Request**

```json
{
  "operation": "select",
  "table": "Person",
  "columns": ["COUNT(*) AS total"],
  "where": {"field": "Last_Name", "operator": "LIKE", "value": "S%"}
}
```

---

## execute_write_query

Runs a single Data Manipulation Language statement — `INSERT`, `UPDATE`, `DELETE`, or `MERGE`.
Registered only when `query_mode` is `read-write`.

Every call is checked for the `mcp:write` scope and then submitted for human approval before it
reaches the database. See [Write support](../write-support.md).

!!! tip "A conditional write is counted before approval"
    For an `UPDATE` or `DELETE` with a `WHERE` clause, the server runs `SELECT COUNT(*)` with the
    same predicate first and states the result in the approval prompt:

    ```
    DML (58 row(s) currently match): DELETE FROM Person WHERE Last_Name LIKE 'S%'
    ```

    A `WHERE` clause looks the same regardless of how many rows it matches, so the count is what
    makes the approval decision meaningful. It is an estimate taken just before execution, and it is
    best effort — a statement the server cannot analyze still reaches the prompt, showing the
    statement text alone.

!!! note "Statements rejected before anyone is asked to approve them"
    - `UPDATE` and `DELETE` without a `WHERE` clause
    - Writes to the Zen system catalog (`X$` tables)
    - Multiple statements in one call
    - Data Definition Language — deferred, not permitted in this release

    The server refuses these statements on inspection, so no approval prompt appears. A missing prompt therefore does
    not by itself mean the write was declined.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `sql` | `string` | ✓ | The DML statement to execute. |

### Output Schema

**On Success**

```json
{
  "sql": "<statement>",
  "rows_affected": 1,
  "success": true,
  "method": "execute_write_query"
}
```

**When the caller lacks the write scope**

```json
{
  "error": "write operations require the 'mcp:write' scope, which the access token does not carry"
}
```

### Example

**Request**

```json
{
  "sql": "UPDATE Person SET Last_Name = 'Sanderson' WHERE ID = 102"
}
```

**Response**

```json
{
  "sql": "UPDATE Person SET Last_Name = 'Sanderson' WHERE ID = 102",
  "rows_affected": 1,
  "success": true,
  "method": "execute_write_query"
}
```

---

## blob_operation

Lists and downloads file or blob data from tables that store binary content.

!!! note "Read-only mode only"
    This tool is not registered when `query_mode` is `read-write`.

### Parameters

**Required**

| Field | Type | Description |
|-------|------|-------------|
| `action` | `string` | One of: `list`, `download`. |
| `table_name` | `string` | Table that stores blob data. |

**Optional**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `file_id` | `integer` | — | Row identifier. Required when `action` is `download`. |
| `output_path` | `string` | — | Destination file path. Required when `action` is `download`. |
| `id_column` | `string` | `id` | Name of the ID column. |
| `blob_column` | `string` | `file_data` | Name of the blob column. |

### Output Schema

**For `list`**

```json
{
  "files": [{"id": "<row_id>", "filename": "<filename>"}],
  "count": "<num_files>"
}
```

**For `download`**

```json
{
  "success": true,
  "output_path": "<destination_path>",
  "size": "<file_size_bytes>"
}
```

### Example

**Request**

```json
{
  "action": "list",
  "table_name": "documents"
}
```

**Response**

```json
{
  "files": [{"id": 1, "filename": "report.pdf"}],
  "count": 1
}
```

---

## database_manage

Provides server management operations: list available databases, list DSNs with details, query server capabilities, and release locks.

!!! note "Read-only mode only"
    This tool is not registered when `query_mode` is `read-write`.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `action` | `string` | ✓ | One of: `list`, `list_dsns`, `capabilities`, `release_locks`. |

### Output Schema

**For `capabilities`**

```json
{
  "server": "Actian Zen",
  "features": ["sql", "blobs"]
}
```

**For `list_dsns`**

```json
{
  "current_dsn": "<active_dsn>",
  "available_dsns": {
    "<dsn_name>": {"driver": "<driver_name>"}
  },
  "count": "<num_dsns>"
}
```

### Example

**Request**

```json
{
  "action": "capabilities"
}
```

**Response**

```json
{
  "server": "Actian Zen",
  "features": ["sql", "blobs"]
}
```

---

## Next Steps

<div class="grid cards" markdown>

- :material-folder-open: **[Resources](../resources/index.md)**  
  Explore the resource types available through the Zen server.

- :material-message-text: **[Prompts](../prompts/index.md)**  
  Use the built-in prompt templates for common workflows.

- :material-pencil: **[Write support](../write-support.md)**  
  Turn on `query_mode`, and see the scope and approval checks every write passes.

</div>