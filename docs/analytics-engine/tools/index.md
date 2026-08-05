---
title: Tools
description: Built-in tools available when using the Actian MCP Server with Actian Analytics Engine.
---

# Tools

The Actian MCP Server for the Actian Analytics Engine provides four built-in tools for database discovery and query execution.


## Available Tools

Use the following tools to interact with the database:


| Tool | Description |
|------|-------------|
| [`execute_query`](#execute_query) | Runs a SQL query against the connected database. Reads always, writes when the server permits them. |
| [`list_tables`](#list_tables) | Lists all available user tables and views. |
| [`describe_table`](#describe_table) | Returns column definitions and comments for a specific table. |
| [`list_functions`](#list_functions) | Lists available user-defined functions and procedures. |


## execute_query

--8<-- "tools/execute-query-sql.md"

### Example: Writing a Row

This example needs `query_mode` set to `read-write`.

**Request**

```
Add a customer named Contoso Supply
```

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

--8<-- "tools/describe-table.md"

## list_functions

--8<-- "tools/list-functions.md"

## Next Steps

<div class="grid cards" markdown>

- :material-folder-open: **[Resources](../resources/index.md)**  
  Explore the resource types available through the server.

- :material-message-text: **[Prompts](../prompts/index.md)**  
  Use the built-in prompt templates for common workflows.

</div>