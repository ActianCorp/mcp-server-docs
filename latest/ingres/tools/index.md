---
title: Tools
description: Overview of the tools available when using the Actian MCP Server with Actian Ingres.
---

# Tools

The Actian MCP Server for Actian Ingres provides built-in tools that allow you to discover databases, run queries, and check the operational health of the Ingres installation.

## Available Tools

Use the following tools to interact with the database:

| Tool | Description |
|------|-------------|
| [`execute_query`](#execute_query) | Runs a SQL query against the connected database. Reads run at any time; writes run only when the server permits them. |
| [`list_tables`](#list_tables) | Lists all available user tables and views, with each one's owner and whether it is a table or a view. |
| [`describe_table`](#describe_table) | Displays column definitions and comments for a given table. |
| [`list_indexes`](#list_indexes) | Lists the indexes defined on a given table, with their columns in key order. |
| [`list_functions`](#list_functions) | Lists available user-defined functions and procedures. |

The server also provides seven read-only operational health tools. See [Operational health tools](#operational-health-tools).

## execute_query

Use this tool to run a SQL query against Actian Ingres. The server returns the result set as structured `JSON`.

By default the tool accepts only `SELECT`. When the server runs with `query_mode` set to `read-write`, it also accepts the Data Manipulation Language (DML) statements `INSERT`, `UPDATE`, `DELETE`, and `MERGE`. See [Write support](../write-support.md).

!!! note "Result truncation:"
    If the number of rows exceeds the `max_rows` configuration, the response includes the `truncated` and `warning` fields.

!!! warning "Data Definition Language is never permitted"
    This tool does not run Data Definition Language (DDL) or administrative statements in any mode. `CREATE`, `ALTER`, `DROP`, `GRANT`, `SET`, `ENABLE`, `DISABLE`, and `SELECT ... INTO` are rejected. Use Ingres tooling for schema changes.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `query` | `string` | ✓ | The SQL query you want to execute. `SELECT` is always accepted. `INSERT`, `UPDATE`, `DELETE`, and `MERGE` require `query_mode` set to `read-write`. |

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
Show me all the rows in the customers table
```

**Input**

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

### Example: Writing a Row

This example requires `query_mode` set to `read-write`.

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

Before running the statement, the server asks you to approve it in the client. The response depends on your answer.

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

The following errors apply when `query_mode` is `read-write`.

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
	"error": "DDL and administrative statements (CREATE/ALTER/DROP/GRANT/COPY/SET/ENABLE/...) are not permitted."
}
```

## list_tables

Returns all user tables and views available in the connected database as structured JSON. Each row states the object's owner and whether it is a table or a view.

Indexes are not listed. Use [`list_indexes`](#list_indexes) to list the indexes on a table.

### Parameters

This tool does not require input parameters.

### Output Schema

**On Success**

```json
{
	"success": true,
	"columns": ["table_name", "table_owner", "table_type"],
	"rows": [["<table_name>", "<table_owner>", "<table_type>"]],
	"row_count": 1
}
```

`table_type` is `table` or `view`. `table_owner` is the user that owns the table or view. Use it to qualify the name in [`describe_table`](#describe_table), for example `actian.customers`, when tables owned by different users share a name.

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
Show me all the tables in my database
```

**Response**

```json
{
	"success": true,
	"columns": ["table_name", "table_owner", "table_type"],
	"rows": [
		["customers", "actian", "table"],
		["orders", "actian", "table"],
		["open_orders", "actian", "view"]
	],
	"row_count": 3
}
```

## describe_table

Returns schema details for a table, including column names, data types, lengths, scales, and column comments.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `table_name` | `string` | ✓ | Name of the table to describe. Accepts a plain name, such as `orders`, or an owner-qualified name, such as `actian.customers`. |

!!! tip "Qualify the name when several owners have the same table"
    Given a plain name, the server describes the table you own if one exists with that name. Otherwise it selects one belonging to another owner. Pass `owner.table` to describe a specific one.

### Output Schema

**On Success**

```json
{
	"success": true,
	"columns": [
		"table_owner",
		"column_name",
		"column_datatype",
		"column_length",
		"column_scale",
		"column_comment"
	],
	"rows": [["<table_owner>", "<column_name>", "<column_datatype>", "<column_length>", "<column_scale>", "<column_comment>"]],
	"row_count": "<num_rows>",
	"other_owners": ["<owner>"],
	"hint": "<hint>"
}
```

`other_owners` and `hint` are present only when you pass a plain name and tables with that name belong to more than one owner. `other_owners` lists the owners that were not described; call the tool again with `owner.table` to describe one of those.

If no table matches the name, or you cannot see it, the response succeeds with an empty `rows` list and a `row_count` of `0`.

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
		"table_owner",
		"column_name",
		"column_datatype",
		"column_length",
		"column_scale",
		"column_comment"
	],
	"rows": [
		["actian", "customer_id", "integer", "4", "0", "Primary key"],
		["actian", "customer_name", "varchar", "100", "0", "Customer display name"]
	],
	"row_count": 2
}
```

**Error Response**

```json
{
	"success": false,
	"error": "No permission to access table 'iirelation'"
}
```

The server rejects requests to describe Ingres system catalog tables, whose names begin with `ii`.

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

## list_indexes

Returns the indexes defined on a single table as structured JSON, including each index's columns in key order.

The tool reports two kinds of index:

| Kind | `index_kind` value | Created by |
|------|--------------------|------------|
| User-created | `user` | `CREATE INDEX` |
| System-generated | `generated` | A `PRIMARY KEY` or `UNIQUE` constraint |

By default, only system-generated indexes are listed. Pass `user` as `true` to include user-created indexes. Indexes that Ingres maintains on its own system catalogs are never listed.

### Parameters

| Field | Type | Required | Default | Description |
|-------|------|:--------:|---------|-------------|
| `table_name` | `string` | ✓ | — | Name of the table whose indexes to list. Accepts a plain name, such as `orders`, or an owner-qualified name, such as `actian.orders`. |
| `user` | `boolean` | | `false` | Include user-created indexes, that is, those created with `CREATE INDEX`. |
| `system_generated` | `boolean` | | `true` | Include system-generated indexes, that is, those created for `PRIMARY KEY` or `UNIQUE` constraints. |

!!! tip "Qualify the name when several owners have the same table"
    A plain name resolves the same way as in [`describe_table`](#describe_table). When tables with that name belong to more than one owner, the response includes `other_owners` and `hint`. Pass `owner.table` to list the indexes of a specific one.

### Output Schema

**On Success**

```json
{
	"success": true,
	"columns": [
		"index_name",
		"table_name",
		"table_owner",
		"index_owner",
		"index_kind",
		"is_unique",
		"storage_structure",
		"index_columns"
	],
	"rows": [["<index_name>", "<table_name>", "<table_owner>", "<index_owner>", "<index_kind>", "<is_unique>", "<storage_structure>", [{"name": "<column_name>", "direction": "<direction>"}]]],
	"row_count": "<num_rows>"
}
```

| Column | Description |
|--------|-------------|
| `index_name` | Name of the index. |
| `table_name`, `table_owner` | The table the index is defined on, and its owner. |
| `index_owner` | Owner of the index. |
| `index_kind` | `user` or `generated`. |
| `is_unique` | `Y` or `N`. |
| `storage_structure` | The storage structure the index was built with: `ISAM` (the default), `BTREE`, `HASH`, or `RTREE`. |
| `index_columns` | The index's columns in key order, each as `{"name", "direction"}`. Key order determines whether the index can serve a query that filters on a leading subset of the columns. The list is empty for an index whose columns the catalog does not record. |

A table with no matching indexes returns success with an empty `rows` list. If you set both `user` and `system_generated` to `false`, the response is also empty and includes a `hint` that says so.

If the index column list exceeds the `max_rows` limit, the response includes `truncated` and a `warning`, and some indexes show only their leading columns.

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
Show me all the indexes on the orders table
```

**Input**

```json
{
	"table_name": "orders",
	"user": true
}
```

**Response**

```json
{
	"success": true,
	"columns": [
		"index_name",
		"table_name",
		"table_owner",
		"index_owner",
		"index_kind",
		"is_unique",
		"storage_structure",
		"index_columns"
	],
	"rows": [
		["<generated_index_name>", "orders", "actian", "actian", "generated", "Y", "BTREE", [{"name": "order_id", "direction": "A"}]],
		["orders_by_customer", "orders", "actian", "actian", "user", "N", "ISAM", [{"name": "customer_id", "direction": "A"}, {"name": "order_date", "direction": "A"}]]
	],
	"row_count": 2
}
```

## list_functions

Returns user-defined functions and procedures, including their stored definitions, as structured JSON.

### Parameters

This tool does not require input parameters.

### Output Schema

**On Success**

```json
{
	"success": true,
	"columns": ["function_name", "function_ddl"],
	"rows": [["<function_name>", "<function_ddl>"]],
	"row_count": 1
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

## Operational Health Tools

The following read-only tools report the operational health of the Ingres installation and the connected database. They take no parameters and return a common result format in which each value carries its status (`ok`, `warn`, `crit`, or `info`) and the threshold that judged it. For the result format, thresholds, and the `health` configuration block, see [Health tools](../health-tools.md).

| Tool | Scope | Reports |
|------|-------|---------|
| [`server_status`](../health-tools.md#server_status) | Installation | Whether the connected database is reachable, plus Ingres server state, connections, and start time. |
| [`checkpoint_journal_health`](../health-tools.md#checkpoint_journal_health) | Database | Checkpoint age and user tables that are not journaled. |
| [`locking_health`](../health-tools.md#locking_health) | Installation | Lock capacity, live locks, and deadlock and lock-wait counters. |
| [`long_running_queries`](../health-tools.md#long_running_queries) | Database | Queries running now and how long each has run. |
| [`cache_io_health`](../health-tools.md#cache_io_health) | Installation | Buffer cache activity and log writer pressure. |
| [`storage_health`](../health-tools.md#storage_health) | Database | Tables with the most overflow and over-allocated pages. |
| [`optimizer_health`](../health-tools.md#optimizer_health) | Database | Drift between current row counts and optimizer statistics. |

## Tool Annotations

Each tool declares MCP tool annotations. Clients can use these hints, for example, to decide whether to run a tool without asking you first.

| Tool | `readOnlyHint` | `destructiveHint` | `idempotentHint` | `openWorldHint` |
|------|:--------------:|:-----------------:|:----------------:|:---------------:|
| `execute_query`, when `query_mode` is `read-only` | `true` | — | `true` | `false` |
| `execute_query`, when `query_mode` is `read-write` | `false` | `true` | `false` | `false` |
| `list_tables`, `describe_table`, `list_indexes`, `list_functions` | `true` | — | `true` | `false` |
| All seven health tools | `true` | — | `true` | `false` |

`destructiveHint` is not declared on read-only tools, because it applies only when `readOnlyHint` is `false`.

!!! note "Annotations are hints, not a security control"
    Annotations describe how a tool behaves so that a client can make a sensible choice. They do not enforce anything. Writes are controlled by `query_mode`, the `mcp:write` scope, and human approval, as described in [Write support](../write-support.md), and database privileges always apply.

## Next Steps

<div class="grid cards" markdown>

- :material-heart-pulse: **[Health Tools](../health-tools.md)**  
  Check checkpoint, locking, cache, storage, and optimizer health, and tune the thresholds.

- :material-folder-open: **[Resources](../resources/index.md)**  
  Explore the resource types available through the MCP Server for Ingres.

- :material-chat-processing: **[Prompts](../prompts/index.md)**  
  Use pre-built prompt templates for common Ingres workflows.

</div>
