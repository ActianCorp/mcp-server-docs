---
title: Tools
description: Built-in tools available when using the Actian MCP Server with Actian Analytics Engine.
---

# Tools

The Actian MCP Server for the Actian Analytics Engine provides four built-in tools for database discovery and read-only query execution.


## Available Tools

Use the following tools to interact with the database:


| Tool | Description |
|------|-------------|
| [`execute_query`](#execute_query) | Runs a read-only SQL query against the connected database. |
| [`list_tables`](#list_tables) | Lists all available user tables and views. |
| [`describe_table`](#describe_table) | Returns column definitions and comments for a specific table. |
| [`list_functions`](#list_functions) | Lists available user-defined functions and procedures. |


## execute_query

Use this tool to run read-only SQL queries. The server returns the result set as a structured JSON object.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `query` | `string` | ✓ | Read-only SQL query to execute. |

### Output Schema

**On Success**

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
    The `truncated` and `warning` fields appear only when the number of result rows exceeds the `max_rows` value set in the server configuration.

**On Error**

```json
{
  "success": false,
  "error": "<error_message>"
}
```

### Example

**Request**

```
Show me all the rows in the customers table
```

```json
{
  "query": "SELECT * FROM customers"
}
```

**Response**

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


## list_tables

Returns all user tables and views available in the connected database as structured JSON.

### Parameters

This tool takes no input parameters.

### Output Schema

**On Success**

```json
{
  "success": true,
  "columns": ["table_name"],
  "rows": [["<table_name>"]],
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

**Request**

```
Show me all the tables in my database
```

**Response**

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

Returns schema details for a specific table, including column names, data types, lengths, scales, and comments.

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
    "column_scale",
    "column_comment"
  ],
  "rows": [
    ["<column_name>", "<column_datatype>", "<column_length>", "<column_scale>", "<column_comment>"]
  ],
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

**Request**

```
Show me schema information about the customers table
```

```json
{
  "table_name": "customers"
}
```

**Response**

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

!!! warning
    If the authenticated database user lacks access to a table, the error response includes a permission message. For example: `"error": "No permission to access table 'ii_tables'"`.



## list_functions

Returns user-defined functions and procedures, including their stored DDL definitions, as structured JSON.

### Parameters

This tool takes no input parameters.

### Output Schema

**On Success**

```json
{
  "success": true,
  "columns": ["function_name", "function_ddl"],
  "rows": [["<function_name>", "<function_ddl>"]],
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

**Request**

```
Show me all the functions in my database
```

**Response**

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


## Next Steps

<div class="grid cards" markdown>

- :material-folder-open: **[Resources](../resources/index.md)**  
  Explore the resource types available through the server.

- :material-message-text: **[Prompts](../prompts/index.md)**  
  Use the built-in prompt templates for common workflows.

</div>