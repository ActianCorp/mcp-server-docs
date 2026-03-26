---
title: Zen Tools
description: MCP tools available in the Zen plugin — query execution, ORM operations, DDL, transactions, and guardrails.
---

# Zen Tools

The Zen plugin exposes MCP tools that AI agents call to interact with Actian Zen databases. In readonly mode (the default) 6 tools are registered. With write access enabled, 3 additional tools become available.

---

## Readonly Tools (always available)

| Tool | Description |
|------|-------------|
| `execute_query` | Run a SQL SELECT query against the connected database |
| `list_tables` | List all user tables (system tables excluded) |
| `describe_table` | Get column names, types, nullability, and primary keys for a table |
| `orm_operation` | Structured CRUD via SQLAlchemy — supports JOINs, filtering, ordering |
| `blob_operation` | Read binary/file attachment columns |
| `database_manage` | List DSNs, query engine capabilities, release locks |

## Write Tools (readonly=false only)

| Tool | Description |
|------|-------------|
| `ddl_operation` | Schema changes: create/drop tables, columns, indexes, views, procedures, triggers |
| `batch_operation` | Row counts with WHERE filters |
| `transaction` | Explicit begin / commit / rollback with 5-minute timeout |

---

## execute_query

Runs a raw SQL SELECT statement.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `sql` | string | yes | The SQL SELECT statement to execute |

### Zen SQL Dialect Notes

Zen/PSQL has a distinct SQL dialect. Key differences from standard SQL:

- Use `CHAR_LENGTH()` instead of `LEN()` — the server auto-translates `LEN()` calls
- **No CTEs** (`WITH ... AS` is not supported)
- **No window functions** (`ROW_NUMBER()`, `RANK()`, etc.)
- `IDENTITY` columns instead of `AUTOINCREMENT` or `SERIAL`
- Constraint names are limited to **20 characters** — the server auto-truncates
- **No string concatenation with `+`** — use Zen's concat syntax
- `INFORMATION_SCHEMA` queries are translated to `dbo.fSQL*` function calls automatically

### Example

```json
{
  "sql": "SELECT First_Name, Last_Name FROM Person WHERE ID < 100"
}
```

---

## orm_operation

Structured data access through SQLAlchemy. Preferred over `execute_query` for CRUD because it handles Zen SQL quirks (type mapping, IDENTITY columns, constraint naming) automatically.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `table` | string | yes | Target table name |
| `operation` | string | yes | One of: `select`, `insert`, `update`, `delete` |
| `columns` | array | no | Columns to return (select) |
| `where` | object | no | Filter conditions as key-value pairs |
| `values` | object | no | Data for insert/update |
| `order_by` | string | no | Column to sort by |
| `limit` | integer | no | Max rows to return |
| `joins` | array | no | JOIN specifications |

### JOIN example

```json
{
  "table": "Student",
  "operation": "select",
  "columns": ["Student.ID", "Person.First_Name", "Person.Last_Name"],
  "joins": [
    {
      "table": "Person",
      "on": "Student.ID = Person.ID",
      "type": "inner"
    }
  ],
  "limit": 10
}
```

Using `orm_operation` with the `joins` parameter is preferred over writing raw JOIN SQL in `execute_query`, because it avoids Zen dialect pitfalls.

---

## ddl_operation

Schema modification tool. Only available when `readonly=false`.

### Modes

| Mode | Description |
|------|-------------|
| `create_table` | Create a new table with column definitions |
| `drop_table` | Drop an existing table |
| `add_column` | Add a column to an existing table |
| `drop_column` | Remove a column from a table |
| `create_index` | Create an index on one or more columns |
| `drop_index` | Drop an existing index |
| `create_view` | Create a SQL view |
| `drop_view` | Drop a view |
| `create_procedure` | Create a stored procedure |
| `drop_procedure` | Drop a stored procedure |
| `create_function` | Create a function |
| `drop_function` | Drop a function |
| `create_trigger` | Create a trigger |
| `drop_trigger` | Drop a trigger |

DDL identifiers are validated against injection patterns before execution.

---

## describe_table

Returns column metadata for a table: name, data type, nullability, and primary key membership.

Internally, Zen does not support `INFORMATION_SCHEMA` views. The server translates these queries to Zen's `dbo.fSQL*` catalog functions:

- `INFORMATION_SCHEMA.TABLES` → `dbo.fSQLTables()`
- `INFORMATION_SCHEMA.COLUMNS` → `dbo.fSQLColumns()`
- `INFORMATION_SCHEMA.TABLE_CONSTRAINTS` → `dbo.fSQLSpecialColumns()`
- `INFORMATION_SCHEMA.KEY_COLUMN_USAGE` → `dbo.fSQLStatistics()`

This translation is automatic and transparent to the AI agent.

---

## Readonly Guard

Two layers of protection prevent write operations in readonly mode:

1. **Python SQL parser** — every query submitted to `execute_query` is parsed. Only `SELECT` statements (including subqueries) are allowed. `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`, `CALL`, and multi-statement inputs are rejected before reaching the database.

2. **OPENMODE=1** — the ODBC connection is opened with read-only mode at the engine level. Even if a write statement bypasses the parser, the Zen engine itself rejects it.

---

## Row Cap

All queries are subject to a row limit controlled by the `max_rows` configuration option (default: **1000**).

- If a query returns more than `max_rows` rows, the result is truncated and a `truncation_note` field is added to the response indicating how many rows were omitted.
- If the query contains an explicit `TOP N` clause where N is less than `max_rows`, the explicit limit is honored and no truncation note appears.
- `orm_operation` respects the same cap via its `limit` parameter and the global `max_rows` setting.
