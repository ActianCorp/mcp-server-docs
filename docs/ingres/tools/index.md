---
title: Tools
description: Overview of the tools available when using the Actian MCP Server with Actian Ingres.
---

# Tools

The Actian MCP Server for Actian Ingres provides built-in tools that allow you to discover databases and run queries.

## Available Tools

Use the following tools to interact with the database:

| Tool | Description |
|------|-------------|
| [`execute_query`](#execute_query) | Runs a SQL query against the connected database. Reads always, writes when the server permits them. |
| [`list_tables`](#list_tables) | Lists all available user tables and views. |
| [`describe_table`](#describe_table) | Displays column definitions and comments for a given table. |
| [`list_functions`](#list_functions) | Lists available user-defined functions and procedures. |

## execute_query

--8<-- "tools/execute-query-sql.md"

### Example: Writing a Row

This example needs `query_mode` set to `read-write`.

**User Request**

```
Add a customer named Contoso Supply
```

**Input**

```json
{
	"query": "INSERT INTO customers (customer_id, customer_name) VALUES (103, 'Contoso Supply')"
}
```

Before running the statement, the server asks you to approve it in your client. The response depends on your answer.

**Response, when you approve**

```json
{
	"success": true,
	"columns": [],
	"rows": [],
	"row_count": 1
}
```

**Response, when you decline, do not answer, or the client cannot show the prompt**

```json
{
	"success": false,
	"error": "Write operation was not approved by the user."
}
```

### Write Errors

These apply when `query_mode` is `read-write`.

**The token lacks the `mcp:write` scope**

The server checks the scope before it asks anyone to approve the statement, so no prompt appears.

```json
{
	"success": false,
	"error": "write operations require the 'mcp:write' scope, which the access token does not carry"
}
```

**The statement is DDL or administrative**

```json
{
	"success": false,
	"error": "DDL and administrative statements (CREATE/ALTER/DROP/GRANT/SET/ENABLE/...) are not permitted."
}
```

## list_tables

--8<-- "tools/list-tables.md"

## describe_table

Returns schema details for a table, including column names, data types, lengths, scales, and column comments.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `table_name` | `string` | ✓ | Name of the table to describe. Accepts a plain name, such as `orders`, or an owner-qualified name, such as `actian.customers`. |

!!! tip "Qualify the name when several owners have the same table"
    Given a plain name, the server describes your own table if you own one with that name. Otherwise it picks one of the other owners. Pass `owner.table` to describe a specific one.

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
	"rows": [["<column_name>", "<column_datatype>", "<column_length>", "<column_scale>", "<column_comment>"]],
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
		["customer_id", "integer", "4", "0", "Primary key"],
		["customer_name", "varchar", "100", "0", "Customer display name"]
	],
	"row_count": 2
}
```

**Error Response**

```json
{
	"success": false,
	"error": "No permission to access table 'ii_tables'"
}
```

### Example: Naming the Owner

**User Request**

```
Describe the customers table owned by actian
```

**Input**

```json
{
	"table_name": "actian.customers"
}
```

The response has the same shape as the previous example. If no table matches both the name and the owner, `rows` is empty and `row_count` is `0`.

## list_functions

--8<-- "tools/list-functions.md"

## Next Steps

<div class="grid cards" markdown>

- :material-folder-open: **[Resources](../resources/index.md)**  
  Explore the resource types available through the MCP Server for Ingres.

- :material-chat-processing: **[Prompts](../prompts/index.md)**  
  Use pre-built prompt templates for common Ingres workflows.

</div>
