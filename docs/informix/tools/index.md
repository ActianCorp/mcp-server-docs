---
title: Tools
description: Overview of the tools available when using the Actian MCP Server with Informix database.
---

# Tools

The Actian MCP Server for **Informix Database** exposes a set of built-in tools for database discovery and read-only query execution.

## Available tools

The Informix database integration provides the following tools:

| Tool | Purpose |
|------|---------|
| `execute_query` | Runs a read-only SQL query against the connected database. |
| `list_tables` | Lists available user tables and views. |
| `describe_table` | Shows column definitions and comments for a table. |
| `list_functions` | Lists available user-defined functions and procedures. |

## execute_query

### Description

Executes a read-only SQL query against Informix database and returns the result set as structured JSON.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | `string` | Yes | Read-only SQL query to execute. |

### Output Schema

```json
{
	"success": true,
	"columns": ["<result_columns>"],
	"rows": [["<result_rows>"]],
	"row_count": "<num_rows>",
	"truncated": true,
	"warning": "Results were truncated to <max_rows> rows."
}
```

!!! note
    The `truncated` and `warning` fields appear only when the number of result rows exceeds the `max_rows` configuration.

On error:

```json
{
	"success": false,
	"error": "<error_message>"
}
```

### Example

```
Show me all the rows in the customers table
```

```json
{
	"query": "SELECT * FROM customers"
}
```

### Success Response Example

```json
{
	"success": true,
	"columns": ["customer_id", "customer_email"],
	"rows": [
		[101, "alice@tech.com"],
		[102, "bob@corp.net"]
	],
	"row_count": 2
}
```

## list_tables

### Description

Returns all user tables and views available in the connected database as structured JSON.

### Input Parameters

This tool doesn't require any input parameters.

### Output Schema

```json
{
	"success": true,
	"columns": ["table_name"],
	"rows": [["<table_name>"]],
	"row_count": 1
}
```

On error:

```json
{
	"success": false,
	"error": "<error_message>"
}
```

### Example

```
Show me all the tables in my database
```

This tool takes no input.

### Success Response Example

```json
{
	"success": true,
	"columns": ["table_name"],
	"rows": [
		["customers"],
		["orders"]
	],
	"row_count": 2
}
```

## describe_table

### Description

Returns schema details for a table, including column names, data types, lengths, scales, and column comments.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `table_name` | `string` | Yes | Name of the table to describe. |

### Output Schema

```json
{
	"success": true,
	"columns": [
		"column_name",
		"column_datatype",
		"column_length",
		"null_column",
		"key_type"
	],
	"rows": [["<column_name>", "<column_datatype>", "<column_length>", "<null_column>", "<key_type>"]],
	"row_count": "<num_rows>"
}
```

On error:

```json
{
	"success": false,
	"error": "<error_message>"
}
```

### Example

```
Show me schema information about the customers table
```

```json
{
	"table_name": "customers"
}
```

### Success Response Example

```json
{
	"success": true,
	"columns": [
		"column_name",
		"column_datatype",
		"column_length",
		"column_scale",
		"column_comment"
	],
	"rows": [
		["customer_id", "integer", "4", "YES", "P"],
		["email", "varchar", "50", "NO", "None"]
	],
	"row_count": 2
}
```

### Error Response Example

```json
{
	"success": false,
	"error": "No permission to access table 'table name'"
}
```

## list_functions

### Description

Returns user-defined functions and procedures, including their stored definitions, as structured JSON.

### Input Parameters

This tool doesn't require any input parameters.

### Output Schema

```json
{
	"success": true,
	"columns": ["function_name","type", "function_ddl"],
	"rows": [["<function_name>", "<type>","<function_ddl>"]],
	"row_count": 1
}
```

On error:

```json
{
	"success": false,
	"error": "<error_message>"
}
```

### Example

```
Show me all the functions in my database
```

This tool takes no input.

### Success Response Example

```json
{
	"success": true,
	"columns": ["function_name", "function_ddl"],
	"rows": [
		["calculate_discount","FUNCTION", "CREATE FUNCTION calculate_discount(...) ..."],
		["refresh_sales_summary","PROCEDURE", "CREATE PROCEDURE refresh_sales_summary() ..."]
	],
	"row_count": 2
}
```

## Next steps

- [Resources](../resources/index.md) — Learn about Informix MCP server resources
- [Prompts](../prompts/index.md) — Learn about Informix MCP server prompts