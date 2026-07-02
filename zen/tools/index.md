---
title: Tools
description: Built-in tools available when using the Actian MCP Server with Actian Zen.
---

# Tools

The Actian MCP Server for Actian Zen includes six built-in tools for database access, ORM operations, blob handling, and server management.


## Available Tools

Use the following tools to interact with the database:

| Tool | Description |
|------|-------------|
| [`execute_query`](#execute_query) | Runs read-only SQL with automatic Zen dialect translation. |
| [`list_tables`](#list_tables) | Lists all user tables from the Zen catalog. |
| [`describe_table`](#describe_table) | Returns column metadata, primary keys, and foreign keys for a table. |
| [`orm_operation`](#orm_operation) | Executes structured queries via SQLAlchemy with JOINs, WHERE, ORDER BY, GROUP BY, and LIMIT. |
| [`blob_operation`](#blob_operation) | Lists and downloads file and blob data. |
| [`database_manage`](#database_manage) | Queries server capabilities, lists DSNs, and releases locks. |

---

## execute_query

Executes a read-only SQL query against Actian Zen with automatic dialect translation. It supports complex queries like JOINs, subqueries, aggregations, and UNION.

!!! note "Auto-translations"
    The following translations are applied automatically before execution:

    - `LEN()` → `CHAR_LENGTH()` (Zen does not support `LEN()`)
    - `INFORMATION_SCHEMA` queries → `dbo.fSQL*()` catalog functions
    - Constraint names are truncated to 20 characters (Zen limit)

    Only `SELECT` queries are permitted.

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

Performs structured read queries via SQLAlchemy with dynamic model creation. Handles the Zen SQL dialect automatically.

Supports JOINs (up to 3 tables), WHERE conditions, ORDER BY, GROUP BY, HAVING, LIMIT, OFFSET, and aggregate functions (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`).

### Parameters

**Required**

| Field | Type | Description |
|-------|------|-------------|
| `operation` | `string` | Must be `select`. |
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

## blob_operation

Lists and downloads file or blob data from tables that store binary content.

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

</div>