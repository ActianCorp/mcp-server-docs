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

--8<-- "tools/write-example-sql.md"

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