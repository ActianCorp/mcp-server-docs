---
title: Tools
description: Overview of the tools available when using the Actian MCP Server with HCL Informix® database.
---

# Tools

The Actian MCP Server for HCL Informix® provides built-in tools for database discovery and read-only query execution.

## Available Tools

| Tool | Description |
|------|-------------|
| [`execute_query`](#execute_query) | Runs a read-only SQL query against the connected database. |
| [`list_tables`](#list_tables) | Lists available user tables and views. |
| [`describe_table`](#describe_table) | Displays column definitions, data types, and key information for a table.|
| [`list_functions`](#list_functions) | Lists available user-defined functions and procedures. |

## execute_query

--8<-- "tools/execute-query-sql.md"

## list_tables

--8<-- "tools/list-tables.md"

## describe_table

Returns schema details for a table, including column names, data types, lengths, scales, and column comments.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `table_name` | `string` | ✓ | Name of the table to describe. |

### Output Schema

**On Success**

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

**On Error**

```json
{
	"success": false,
	"error": "<error_message>"
}
```

### Example

**User Request**

```
Show me schema information about the customers table
```

**Input**

```json
{
	"table_name": "customers"
}
```

**Success Response**

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

**Error Response**

```json
{
	"success": false,
	"error": "No permission to access table 'table name'"
}
```

## list_functions

--8<-- "tools/list-functions.md"

## Next Steps

<div class="grid cards" markdown>

- :material-folder-open: **[Resources](../resources/index.md)**  
  Explore the resource types available through the HCL Informix® server.

- :material-chat-processing: **[Prompts](../prompts/index.md)**  
  Use pre-built prompt templates for common HCL Informix® workflows.

</div>