---
title: Tools
description: Overview of the tools available when using the Actian MCP Server with Actian Analytics Engine.
---

# Tools

The Actian MCP Server for **Actian Analytics Engine** exposes a set of built-in tools for database discovery and read-only query execution.

---

## Available Tools

The Analytics Engine integration provides the following tools:

| Tool | Purpose |
|------|---------|
| `execute_query` | Run a read-only SQL query against the connected database |
| `list_tables` | List available user tables and views |
| `describe_table` | Show column definitions and comments for a table |
| `list_functions` | List available user-defined functions and procedures |

---

## execute_query

### Description

Executes a read-only SQL query against Actian Analytics Engine and returns the result set as structured JSON.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | `string` | Yes | Read-only SQL query to execute |

### Output Schema

```json
{
	"success": true,
	"columns": ["<result_columns>"],
	"rows": [["<result_rows>"]],
	"row_count": "<num_rows>",
    // optional args below: only if the number of table rows is bigger than max_rows configuration
	"truncated": true,
	"warning": "Results were truncated to <max_rows> rows."
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
Show me all the rows in the custumers table
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
	"columns": ["customer_id", "customer_name"],
	"rows": [
		[101, "Acme Retail"],
		[102, "Northwind Stores"]
	],
	"row_count": 2
}
```

---

## list_tables

### Description

Returns all user tables and views available in the connected database as structured JSON.

### Input Parameters

This tool does not require any input parameters.

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

---

## describe_table

### Description

Returns schema details for a table, including column names, data types, lengths, scales, and column comments.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `table_name` | `string` | Yes | Name of the table to describe |

### Output Schema

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
	"rows": [["<column_name>", "<column_datatype>", "<column_length>", "<column_scale>", "<column_comment>"]],
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
		["customer_id", "integer", "4", "0", "Primary key"],
		["customer_name", "varchar", "100", "0", "Customer display name"]
	],
	"row_count": 2
}
```

### Error Response Example

```json
{
	"success": false,
	"error": "No permission to access table 'ii_tables'"
}
```

---

## list_functions

### Description

Returns user-defined functions and procedures, including their stored definitions, as structured JSON.

### Input Parameters

This tool does not require any input parameters.

### Output Schema

```json
{
	"success": true,
	"columns": ["function_name", "function_ddl"],
	"rows": [["<function_name>", "<function_ddl>"]],
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
		["calculate_discount", "CREATE FUNCTION calculate_discount(...) ..."],
		["refresh_sales_summary", "CREATE PROCEDURE refresh_sales_summary() ..."]
	],
	"row_count": 2
}
```

---

## Next Steps
- [Resources](../resources/index.md) — Learn about Analytics Engine resources
- [Prompts](../prompts/index.md) — Learn about Analytics Engine prompts
