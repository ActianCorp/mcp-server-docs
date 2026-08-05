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
  Explore the resource types available through the MCP Server for Ingres.

- :material-chat-processing: **[Prompts](../prompts/index.md)**  
  Use pre-built prompt templates for common Ingres workflows.

</div>
