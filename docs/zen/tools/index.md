---
title: Tools
description: Overview of the tools available when using the Actian MCP Server with Actian Zen.
---

# Tools

The Actian MCP Server for **Actian Zen** exposes 6 tools for read-only database access.

## Available tools

| Tool | Purpose |
|------|---------|
| `execute_query` | Run read-only SQL with automatic Zen dialect translation. |
| `list_tables` | List user tables from the Zen catalog. |
| `describe_table` | Get column metadata, primary keys, and foreign keys for a table. |
| `orm_operation` | Structured queries via SQLAlchemy with JOINs, WHERE, ORDER BY, GROUP BY, LIMIT. |
| `blob_operation` | List and download file/blob data. |
| `database_manage` | Server capabilities, list DSNs, release locks. |

---

## execute_query

### Description

Executes read-only SQL against Actian Zen with automatic dialect translation. Suitable for complex queries including JOINs, subqueries, aggregations, and UNION.

Auto-translations applied:

- `LEN()` is translated to `CHAR_LENGTH()` (Zen does not support `LEN()`).
- `INFORMATION_SCHEMA` queries are translated to `dbo.fSQL*()` catalog functions.
- Constraint names are truncated to 20 characters (Zen limit).

Only SELECT queries are allowed.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sql` | `string` | Yes | SQL query to execute. |

### Output Schema

```json
{
    "results": [{"column": "value"}],
    "row_count": 2,
    "method": "execute_query"
}
```

When the result set exceeds `max_rows` (default 1000):

```json
{
    "results": [{"column": "value"}],
    "row_count": 1000,
    "truncated": true,
    "truncation_note": "Results limited to 1000 rows. Use WHERE to narrow results.",
    "method": "execute_query"
}
```

When dialect translation is applied:

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

```json
{
    "sql": "SELECT * FROM Person WHERE Last_Name LIKE 'S%' ORDER BY First_Name"
}
```

### Success Response Example

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

### Description

Returns all user tables in the connected database by querying the Zen `dbo.fSQLTables()` catalog function. System tables are excluded.

### Input Parameters

This tool doesn't require any input parameters.

### Output Schema

```json
{
    "tables": ["table_name"],
    "count": 1
}
```

### Success Response Example

```json
{
    "tables": ["Person", "Department", "Billing", "Student", "Class", "Tuition", "Faculty"],
    "count": 7
}
```

---

## describe_table

### Description

Returns column metadata for a table, including column names, types, precision, scale, nullability, defaults, primary keys, and foreign keys. Uses `dbo.fSQLColumns()`, `dbo.fSQLPrimaryKeys()`, and `dbo.fSQLForeignKeys()` catalog functions internally.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `table` | `string` | Yes | Name of the table to describe. |

### Output Schema

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

### Example

```json
{
    "table": "Person"
}
```

---

## orm_operation

### Description

Performs structured read queries via SQLAlchemy with dynamic model creation. Handles Zen SQL dialect automatically. Supports JOINs (up to 3 tables), WHERE conditions, ORDER BY, GROUP BY, HAVING, LIMIT, OFFSET, and aggregate functions (COUNT, SUM, AVG, MIN, MAX).

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `operation` | `string` | Yes | Must be `select`. |
| `table` | `string` | Yes | Target table name. |
| `columns` | `list` | No | Columns to return. Supports aggregates like `COUNT(*) AS total`. Defaults to all. |
| `where` | `dict` | No | Filter conditions, e.g. `{"field": "salary", "operator": ">", "value": 50000}`. |
| `order_by` | `list` | No | Column names to sort by. |
| `limit` | `int` | No | Maximum rows to return. Capped at `max_rows`. |
| `offset` | `int` | No | Number of rows to skip. |
| `joins` | `list` | No | Join specifications: `[{"table": "dept", "on": "p.dept_id = dept.id", "type": "LEFT"}]`. |
| `group_by` | `list` | No | Columns to group by. |
| `having` | `dict` | No | HAVING conditions for grouped queries. |

### Output Schema

```json
{
    "results": [{"column": "value"}],
    "row_count": 2,
    "method": "orm_operation"
}
```

### Example

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

### Description

List and download file/blob data from tables that store binary content.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | `string` | Yes | One of: `list`, `download`. |
| `table_name` | `string` | Yes | Table that stores blob data. |
| `file_id` | `int` | No | Row identifier (required for `download`). |
| `output_path` | `string` | No | Destination path (required for `download`). |
| `id_column` | `string` | No | Name of the ID column. Defaults to `id`. |
| `blob_column` | `string` | No | Name of the blob column. Defaults to `file_data`. |

### Output Schema

For `list`:

```json
{
    "files": [{"id": 1, "filename": "report.pdf"}],
    "count": 1
}
```

For `download`:

```json
{
    "success": true,
    "output_path": "/tmp/report.pdf",
    "size": 102400
}
```

### Example

```json
{
    "action": "list",
    "table_name": "documents"
}
```

---

## database_manage

### Description

Database management operations: list available databases, list DSNs with details, query server capabilities, and release locks.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | `string` | Yes | One of: `list`, `list_dsns`, `capabilities`, `release_locks`. |

### Output Schema

For `capabilities`:

```json
{
    "server": "Actian Zen",
    "features": ["sql", "blobs"]
}
```

For `list_dsns`:

```json
{
    "current_dsn": "demodata",
    "available_dsns": {"demodata": {"driver": "Pervasive ODBC Interface"}},
    "count": 1
}
```

### Example

```json
{
    "action": "capabilities"
}
```

---

## Next steps

- [Resources](../resources/index.md) — Learn about Zen resources
- [Prompts](../prompts/index.md) — Learn about Zen prompts
