---
title: Tools
description: Overview of the tools available when using the Actian MCP Server with Actian Zen.
---

# Tools

The Actian MCP Server for **Actian Zen** exposes nine tools in full mode. In read-only mode (`readonly=true`), six read-only tools are registered and write operations are blocked.

## Available tools

### Read-only tools (always available)

| Tool | Purpose |
|------|---------|
| `execute_query` | Run SQL with automatic Zen dialect translation. |
| `list_tables` | List user tables from the Zen catalog. |
| `describe_table` | Get column metadata, primary keys, and foreign keys for a table. |
| `orm_operation` | Structured CRUD via SQLAlchemy with JOINs, WHERE, ORDER BY, LIMIT. |
| `blob_operation` | List and download file/blob data. |
| `database_manage` | Server capabilities, list DSNs, release locks. |

### Write-mode tools (when `readonly=false`)

| Tool | Purpose |
|------|---------|
| `ddl_operation` | Schema change operations (create/drop tables, columns, indexes, views, procedures, functions, triggers). |
| `batch_operation` | Bulk insert, update, delete, and row counting. |
| `transaction` | Transaction control: BEGIN, COMMIT, ROLLBACK with timeout. |

---

## execute_query

### Description

Executes raw SQL against Actian Zen with automatic dialect translation. Suitable for complex queries including JOINs, subqueries, aggregations, UNION, and raw DML. For simple single-table CRUD, prefer `orm_operation`. For schema changes, use `ddl_operation`.

Auto-translations applied:

- `LEN()` is translated to `CHAR_LENGTH()` (Zen doesn't support `LEN()`).
- `INFORMATION_SCHEMA` queries are translated to `dbo.fSQL*()` catalog functions.
- `ALTER TABLE ... RENAME TO` is translated to Zen syntax.
- Constraint names are truncated to 20 characters (Zen limit).

In read-only mode, only SELECT queries are allowed.

### Input parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sql` | `string` | Yes | SQL query to execute. |

### Output schema

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

For non-SELECT statements:

```json
{
	"sql": "INSERT INTO customers (name) VALUES ('Acme')",
	"rows_affected": 1,
	"success": true,
	"method": "execute_query"
}
```

On error:

```json
{
	"error": "database error [HY000]"
}
```

### Example

```
Show me all employees with a salary above 50000
```

```json
{
	"sql": "SELECT * FROM Employee WHERE Salary > 50000"
}
```

### Success response example

```json
{
	"results": [
		{"ID": 101, "First_Name": "Alice", "Last_Name": "Smith", "Salary": 65000},
		{"ID": 102, "First_Name": "Bob", "Last_Name": "Jones", "Salary": 72000}
	],
	"row_count": 2,
	"method": "execute_query"
}
```

---

## list_tables

### Description

Returns all user tables in the connected database by querying the Zen `dbo.fSQLTables()` catalog function. System tables are excluded (only `TABLE_TYPE = 'TABLE'` is returned).

!!! note
    Zen uses `dbo.fSQLTables()` for catalog access, not `ii*` system tables used by other Actian products.

### Input parameters

This tool doesn't require any input parameters.

### Output schema

```json
{
	"tables": ["table_name"],
	"count": 1
}
```

On error:

```json
{
	"error": "<error_message>"
}
```

### Example

```
Show me all the tables in my database
```

This tool takes no input.

### Success response example

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

!!! note
    Zen translates `INFORMATION_SCHEMA` queries to `dbo.fSQL*()` catalog functions automatically. Direct use of `X$File` and `X$Field` system tables isn't required.

### Input parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `table` | `string` | Yes | Name of the table to describe. |

### Output schema

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

On error:

```json
{
	"error": "<error_message>"
}
```

### Example

```
Show me the structure of the Person table
```

```json
{
	"table": "Person"
}
```

### Success response example

```json
{
	"table_name": "Person",
	"columns": [
		{"name": "ID", "type": "BIGIDENTITY", "precision": 19, "scale": 0, "nullable": false, "default": null, "primary_key": true},
		{"name": "First_Name", "type": "VARCHAR", "precision": 30, "scale": null, "nullable": true, "default": null, "primary_key": false},
		{"name": "Last_Name", "type": "VARCHAR", "precision": 30, "scale": null, "nullable": true, "default": null, "primary_key": false}
	],
	"primary_keys": ["ID"],
	"foreign_keys": []
}
```

---

## orm_operation

### Description

Performs structured CRUD operations via SQLAlchemy with dynamic model creation. Best for simple SELECT/INSERT/UPDATE/DELETE on one table. Supports SELECT with JOINs (up to 3 tables), WHERE, ORDER BY, GROUP BY, HAVING, LIMIT, and OFFSET.

For JOINs, subqueries, and aggregations, use `execute_query` with raw SQL instead.

In read-only mode, only `select` operations are allowed.

### Input parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `operation` | `string` | Yes | One of: `select`, `insert`, `update`, `delete`. |
| `table` | `string` | Yes | Target table name. |
| `columns` | `list` | No | Columns to return (SELECT only). Defaults to all. |
| `where` | `dict` | No | Filter conditions as key-value pairs. |
| `order_by` | `list` | No | Column names to sort by. Prefix with `-` for descending. |
| `limit` | `int` | No | Maximum rows to return. Capped at `max_rows`. |
| `offset` | `int` | No | Number of rows to skip. |
| `joins` | `list` | No | Join specifications (up to 3 tables). |
| `group_by` | `list` | No | Columns to group by. |
| `having` | `dict` | No | HAVING conditions for grouped queries. |
| `data` | `dict` | No | Row data for `insert` and `update` operations. |
| `entity_id` | `int` | No | Primary key value for `update` and `delete` operations. |

### Output schema

For `select`:

```json
{
	"results": [{"column": "value"}],
	"row_count": 2,
	"method": "orm_operation"
}
```

For `insert`:

```json
{
	"success": true,
	"id": 123,
	"method": "orm_operation"
}
```

On error:

```json
{
	"error": "<error_message>",
	"hint": "Check resource://database/schema for column names. Consider execute_query for complex queries.",
	"alternative": "execute_query"
}
```

### Example

```
Show me all employees in the Sales department ordered by last name
```

```json
{
	"operation": "select",
	"table": "Person",
	"where": {"Department_ID": 100},
	"order_by": ["Last_Name"],
	"limit": 50
}
```

---

## blob_operation

### Description

File and blob data operations. In read-only mode, only `list` and `download` actions are available; `upload` and `delete` are blocked.

### Input parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | `string` | Yes | One of: `upload`, `download`, `list`, `delete`. |
| `table_name` | `string` | Yes | Table that stores blob data. |
| `file_path` | `string` | No | Local file path (required for `upload`). |
| `metadata_fields` | `dict` | No | Additional metadata columns to populate on upload. |
| `file_id` | `int` | No | Row identifier (required for `download` and `delete`). |
| `output_path` | `string` | No | Destination path (required for `download`). |
| `id_column` | `string` | No | Name of the ID column. Defaults to `id`. |
| `blob_column` | `string` | No | Name of the blob column. Defaults to `file_data`. |

### Output schema

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

On error:

```json
{
	"error": "<error_message>"
}
```

### Example

```
List all files in the documents table
```

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

### Input parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | `string` | Yes | One of: `list`, `list_dsns`, `capabilities`, `release_locks`. |
| `dsn_name` | `string` | No | DSN name (used by some actions). |

### Output schema

For `list`:

```json
{
	"current_dsn": "demodata",
	"available_dsns": {"demodata": {"driver": "Pervasive ODBC Interface"}},
	"count": 1
}
```

For `capabilities`:

```json
{
	"server": "Actian Zen",
	"features": ["sql", "transactions", "blobs", "ddl"]
}
```

On error:

```json
{
	"error": "<error_message>"
}
```

### Example

```
What DSNs are available on this server?
```

```json
{
	"action": "list_dsns"
}
```

---

## ddl_operation

### Description

Schema change operations (DDL). Only available when `readonly=false`.

Constraint names are automatically truncated to 20 characters (Zen limit).

### Supported modes

| Mode | Required Parameters | Description |
|------|---------------------|-------------|
| `ddl_create_table` | `table`, `columns` | Create a new table. Optional `zen_options` for engine-specific settings. |
| `ddl_rename_table` | `table`, `new_name` | Rename an existing table. |
| `ddl_alter_table` | `table`, `with_clause` | Alter table with a raw WITH clause. |
| `ddl_drop_table` | `table` | Drop a table. |
| `ddl_add_column` | `table`, `column_name`, `column_type` | Add a column. Optional `length`, `precision`, `scale`. |
| `ddl_drop_column` | `table`, `column_name` | Drop a column. |
| `ddl_create_index` | `table`, `index_name`, `index_columns` | Create an index. |
| `ddl_drop_index` | `table`, `index_name`, `index_columns` | Drop an index. |
| `ddl_drop_fk` | `table`, `constraint_name` | Drop a foreign key constraint. |
| `ddl_create_view` | `name`, `select_clause` | Create a view. |
| `ddl_drop_view` | `name` | Drop a view. |
| `ddl_create_procedure` | `name`, `parameters`, `body` | Create a stored procedure. Optional `atomic`. |
| `ddl_drop_procedure` | `name` | Drop a stored procedure. |
| `ddl_create_function` | `name`, `parameters`, `returns`, `body` | Create a function. |
| `ddl_drop_function` | `name` | Drop a function. |
| `ddl_create_trigger` | `name`, `table`, `timing`, `event`, `body` | Create a trigger. Optional `referencing`, `when`. |
| `ddl_drop_trigger` | `name` | Drop a trigger. |

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mode` | `string` | Yes | DDL mode (see table above). |
| `table` | `string` | Varies | Target table name. |
| `columns` | `list` | Varies | Column definitions for `ddl_create_table`. |
| `zen_options` | `dict` | No | Zen-specific table options (e.g., page size). |
| `new_name` | `string` | Varies | New name for `ddl_rename_table`. |
| `with_clause` | `string` | Varies | Raw WITH clause for `ddl_alter_table`. |
| `column_name` | `string` | Varies | Column name for add/drop column. |
| `column_type` | `string` | Varies | Column data type for `ddl_add_column`. |
| `length` | `int` | No | Column length. |
| `precision` | `int` | No | Column precision. |
| `scale` | `int` | No | Column scale. |
| `index_name` | `string` | Varies | Index name for create/drop index. |
| `index_columns` | `list` | Varies | Columns to index. |
| `constraint_name` | `string` | Varies | Constraint name for `ddl_drop_fk`. |
| `name` | `string` | Varies | Object name for views, procedures, functions, triggers. |
| `parameters` | `list` | Varies | Parameter definitions for procedures and functions. |
| `body` | `string` | Varies | SQL body for procedures, functions, and triggers. |
| `atomic` | `bool` | No | Whether procedure body is atomic. Defaults to `true`. |
| `timing` | `string` | Varies | Trigger timing (`BEFORE`, `AFTER`). |
| `event` | `string` | Varies | Trigger event (`INSERT`, `UPDATE`, `DELETE`). |
| `referencing` | `string` | No | Trigger REFERENCING clause. |
| `when` | `string` | No | Trigger WHEN condition. |
| `returns` | `string` | Varies | Return type for `ddl_create_function`. |
| `select_clause` | `string` | Varies | SELECT statement for `ddl_create_view`. |

### Output schema

```json
{
	"success": true,
	"sql": "CREATE TABLE test_table (id IDENTITY, name VARCHAR(50))",
	"message": "Table created successfully"
}
```

On error:

```json
{
	"error": "<error_message>"
}
```

### Example

```
Create a table called test_reports with id, title, and created_at columns
```

```json
{
	"mode": "ddl_create_table",
	"table": "test_reports",
	"columns": [
		{"name": "id", "type": "IDENTITY"},
		{"name": "title", "type": "VARCHAR", "length": 100},
		{"name": "created_at", "type": "TIMESTAMP"}
	]
}
```

---

## batch_operation

### Description

Bulk data operations and row counting. Only available when `readonly=false`.

### Supported modes

| Mode | Required Parameters | Description |
|------|---------------------|-------------|
| `batch_insert` | `table`, `data` | Insert multiple rows. |
| `batch_update` | `table`, `updates`, `where_clause` | Update rows matching a condition. |
| `batch_delete` | `table`, `where_clause` | Delete rows matching a condition. |
| `count` | `table` | Get row count, with optional `where_clause`. |

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mode` | `string` | Yes | Batch mode (see table above). |
| `table` | `string` | Yes | Target table name. |
| `data` | `list` | Varies | List of row dicts for `batch_insert`. |
| `updates` | `dict` | Varies | Column-value pairs for `batch_update`. |
| `where_clause` | `string` | Varies | WHERE condition (without the `WHERE` keyword). |
| `where_params` | `list` | No | Parameterized values for the WHERE clause. |

### Output schema

For `batch_insert`:

```json
{
	"table": "test_reports",
	"rows_inserted": 3,
	"success": true
}
```

For `count`:

```json
{
	"table": "Person",
	"row_count": 42
}
```

On error:

```json
{
	"error": "<error_message>"
}
```

### Example

```
Insert 3 new employees into the Person table
```

```json
{
	"mode": "batch_insert",
	"table": "Person",
	"data": [
		{"First_Name": "Alice", "Last_Name": "Smith"},
		{"First_Name": "Bob", "Last_Name": "Jones"},
		{"First_Name": "Carol", "Last_Name": "Lee"}
	]
}
```

---

## transaction

### Description

Transaction control. Only available when `readonly=false`. Transactions have a configurable timeout (default 300 seconds); if exceeded, the transaction is automatically rolled back.

### Input parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `action` | `string` | Yes | One of: `begin`, `commit`, `rollback`. |

### Output schema

```json
{
	"success": true,
	"action": "begin",
	"message": "Transaction started"
}
```

On error:

```json
{
	"error": "Unknown action: <action>. Use: begin, commit, rollback"
}
```

### Example

```
Start a transaction, insert a row, then commit
```

```json
{
	"action": "begin"
}
```

---

## Next steps

- [Resources](../resources/index.md) — Learn about Zen resources
- [Prompts](../prompts/index.md) — Learn about Zen prompts
- [Testing](../testing/index.md) — Test coverage and results
