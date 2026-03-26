---
title: API Reference
description: Complete reference for the Actian Zen MCP Server tools, resources, and prompts.
---

# API Reference

---

## Tools

### Readonly Tools (6)

Available in both readonly and full mode.

| Tool | Parameters | Description |
|------|------------|-------------|
| `execute_query` | `sql: str` | Execute a SQL SELECT query. Results capped at `max_rows` (default 1000). |
| `list_tables` | — | List all user tables. System tables (X$*) excluded. |
| `describe_table` | `table: str` | Column names, types, nullability, primary keys. |
| `orm_operation` | `operation: str`, `table: str`, `joins?: list`, `where?: dict`, `order_by?: list`, `limit?: int`, `columns?: list`, `group_by?: list`, `data?: dict` | Structured CRUD with JOINs. Handles Zen SQL dialect automatically. |
| `blob_operation` | `action: str`, `table?: str`, `column?: str` | List and download binary/text file attachments. |
| `database_manage` | `action: str` | List DSNs, check capabilities, release locks. |

### Write Tools (+3, full mode only)

Registered when `readonly: false`.

| Tool | Parameters | Description |
|------|------------|-------------|
| `ddl_operation` | `mode: str`, varies by mode | Schema changes: CREATE/ALTER/DROP TABLE, INDEX, VIEW, PROCEDURE, FUNCTION, TRIGGER. Constraint names auto-truncated to 20 chars. |
| `batch_operation` | `table: str`, `mode: str`, `where?: str` | Batch operations: row count with optional WHERE filter. |
| `transaction` | `action: str` | Transaction management: begin, commit, rollback. 5-minute timeout with auto-rollback. |

---

## Resources

| URI | Description |
|-----|-------------|
| `resource://database/schema` | Full schema: table names, column definitions, primary keys, summary. Injected into server instructions at startup. |

---

## Prompts

| Prompt | Arguments | Description |
|--------|-----------|-------------|
| `ask_question` | `question: str` | General database question prompt. |

---

## orm_operation Details

### select with JOINs

```json
{
    "operation": "select",
    "table": "employees",
    "columns": ["first_name", "last_name", "department_name"],
    "joins": [{"table": "departments", "on": "department_id"}],
    "where": {"status": "active"},
    "order_by": ["last_name"],
    "limit": 50
}
```

### insert

```json
{
    "operation": "insert",
    "table": "employees",
    "data": {"first_name": "John", "last_name": "Smith", "salary": 85000}
}
```

### update / delete

```json
{
    "operation": "update",
    "table": "employees",
    "entity_id": 42,
    "data": {"salary": 90000}
}
```

---

## ddl_operation Modes

| Mode | Required Parameters | Description |
|------|-------------------|-------------|
| `ddl_create_table` | `table`, `columns` | Create table with typed columns |
| `ddl_drop_table` | `table` | Drop table |
| `ddl_rename_table` | `table`, `new_name` | Rename table |
| `ddl_add_column` | `table`, `column_name`, `column_type` | Add column |
| `ddl_drop_column` | `table`, `column_name` | Drop column |
| `ddl_create_index` | `table`, `columns`, `index_name` | Create index |
| `ddl_drop_index` | `index_name` | Drop index |
| `ddl_create_view` | `view_name`, `query` | Create view from SELECT |
| `ddl_drop_view` | `view_name` | Drop view |
| `ddl_create_procedure` | `name`, `parameters`, `body` | Create stored procedure |
| `ddl_drop_procedure` | `name` | Drop procedure |
| `ddl_create_function` | `name`, `parameters`, `returns`, `body` | Create function |
| `ddl_drop_function` | `name` | Drop function |
| `ddl_create_trigger` | `name`, `table`, `timing`, `event`, `body` | Create trigger |
| `ddl_drop_trigger` | `name` | Drop trigger |

---

## Zen SQL Dialect

The server automatically handles Zen-specific SQL:

- `CHAR_LENGTH()` instead of `LEN()`
- No CTEs (`WITH` clause) — rewritten as subqueries
- No window functions — use `orm_operation` with `group_by`
- `IDENTITY` columns (not `SERIAL` or `AUTO_INCREMENT`)
- Table/constraint names: max 20 characters
- `INFORMATION_SCHEMA` queries translated to `dbo.fSQLTables()`, `dbo.fSQLColumns()`, etc.
- String concat: not supported via `+`, `||`, or multi-arg `CONCAT()`

---

## Readonly Mode

When `readonly: true` (default):

- Only 6 tools registered (ddl_operation, batch_operation, transaction excluded)
- `execute_query` rejects INSERT, UPDATE, DELETE, CREATE, DROP, ALTER
- `orm_operation` rejects insert, update, delete
- Zen OPENMODE=1 set on ODBC connection as backup guard
- `blob_operation` rejects upload and delete

---

## Error Handling

All tools return JSON. Errors include:

```json
{
    "error": "database error [42000]",
    "hint": "Check resource://database/schema for column names.",
    "alternative": "execute_query"
}
```

Row-capped results include:

```json
{
    "results": ["..."],
    "truncation_note": "Results limited to 1000 rows. Use WHERE to narrow results."
}
```
