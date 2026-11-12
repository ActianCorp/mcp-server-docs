---
title: Tools
description: Built-in tools available when using the Actian MCP Server with Actian Analytics Engine.
---

# Tools

The Actian MCP Server for the Actian Analytics Engine provides five built-in tools for database discovery, query execution, and vector similarity search.


## Available Tools

Use the following tools to interact with the database:


| Tool | Description |
|------|-------------|
| [`execute_query`](#execute_query) | Runs a SQL query against the connected database. Reads run at any time; writes run only when the server permits them. |
| [`list_tables`](#list_tables) | Lists all available user tables and views, with each one's owner and whether it is a table or a view. |
| [`describe_table`](#describe_table) | Returns column definitions and comments for a specific table. |
| [`list_functions`](#list_functions) | Lists available user-defined functions and procedures. |
| [`vector_search`](#vector_search) | Returns the rows whose `VECTOR` column is most similar to a query vector. Requires Analytics Engine 8.0 or later. |

!!! note "Ingres-only tools"
    The `list_indexes` tool and the operational health tools are available for Ingres only. The Analytics Engine server does not provide them.

### Tool Annotations

Each tool advertises Model Context Protocol (MCP) tool annotations. Clients can use these hints, for example, to decide whether to ask you before running a call.

| Tool | Annotations |
|------|-------------|
| `list_tables`, `describe_table`, `list_functions`, `vector_search` | `readOnlyHint: true`, `idempotentHint: true`, `openWorldHint: false` |
| `execute_query`, with `query_mode` set to `read-only` | `readOnlyHint: true`, `idempotentHint: true`, `openWorldHint: false` |
| `execute_query`, with `query_mode` set to `read-write` | `readOnlyHint: false`, `destructiveHint: true`, `idempotentHint: false`, `openWorldHint: false` |

!!! warning "Annotations are hints, not security controls"
    Annotations describe how a tool behaves. They do not enforce anything, and a client is free to ignore them. What a call can do is decided by the server: `query_mode`, the `mcp:write` scope, write approval, and the database user's own privileges. See [Write Support](../write-support.md).


## execute_query

Use this tool to run SQL queries. The server returns the result set as a structured JSON object.

By default the tool accepts only `SELECT`. When the server runs with `query_mode` set to `read-write`, it also accepts the Data Manipulation Language (DML) statements `INSERT`, `UPDATE`, `DELETE`, and `MERGE`. See [Write support](../write-support.md).

!!! warning "Data Definition Language is never permitted"
    This tool does not run Data Definition Language (DDL) or administrative statements in any mode. `CREATE`, `ALTER`, `DROP`, `GRANT`, `SET`, `ENABLE`, `DISABLE`, and `SELECT ... INTO` are rejected. Use Analytics Engine tooling for schema changes.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `query` | `string` | ✓ | SQL query to execute. `SELECT` is always accepted. `INSERT`, `UPDATE`, `DELETE`, and `MERGE` require `query_mode` set to `read-write`. |

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

### Example: Writing a Row

This example requires `query_mode` set to `read-write`.

**Request**

```
Add a customer named Contoso Supply
```

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

Returns all user tables and views available in the connected database as structured JSON. Each row reports the object's owner and whether it is a table or a view.

### Parameters

This tool takes no input parameters.

### Output Schema

**On Success**

```json
{
  "success": true,
  "columns": ["table_name", "table_owner", "table_type"],
  "rows": [["<table_name>", "<table_owner>", "<table_type>"]],
  "row_count": "<num_rows>"
}
```

`table_type` is `table` or `view`. External tables are reported as `table`. Indexes are not listed. `table_owner` is the user that owns the table or view. Use it to qualify the name in [`describe_table`](#describe_table), for example `actian.customers`, when tables owned by different users share a name.

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
  "columns": ["table_name", "table_owner", "table_type"],
  "rows": [
    ["customers", "actian", "table"],
    ["orders", "actian", "table"],
    ["recent_orders", "actian", "view"]
  ],
  "row_count": 3
}
```


## describe_table

Returns schema details for a specific table, including the owner, column names, data types, lengths, scales, and comments. For a table with a `VECTOR` column, it also reports each vector's dimension, element type, and index.

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
  "rows": [
    ["<table_owner>", "<column_name>", "<column_datatype>", "<column_length>", "<column_scale>", "<column_comment>"]
  ],
  "row_count": "<num_rows>"
}
```

When the name is not owner-qualified and tables with that name belong to more than one owner, the response also includes `other_owners`, a list of the other owners, and a `hint` explaining how to describe one of them.

**Vector Columns**

On Analytics Engine 8.0 and later, a table that has at least one `VECTOR` column returns four additional fields in every row:

| Field | Description |
|-------|-------------|
| `vector_dimensions` | Number of coordinates in the vector. |
| `vector_element_type` | Coordinate type, such as `INTEGER`, `FLOAT4`, or `DECIMAL(5,2)`. |
| `vector_index_name` | Name of the index that covers the column, or `null`. |
| `vector_index_status` | `indexed`, or `no index; queries scan the table`. |

For the vector column itself, `column_datatype` is `VECTOR`. For the table's other columns, the four fields are `null`. Tables without a `VECTOR` column, and servers earlier than Analytics Engine 8.0, return the six fields shown above. See [Vector Search](../vector-search.md#in-describe_table) for an example.

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

!!! warning
    The server refuses any table name that begins with `ii`, the prefix of the system catalog tables, with a permission error. For example: `"error": "No permission to access table 'iitables'"`.

### Example: Naming the Owner

**Request**

```
Describe the customers table owned by actian
```

```json
{
  "table_name": "actian.customers"
}
```

The response has the same shape as the previous example.

!!! note "A table that does not exist"
    If no table matches the name, or the name and owner, the response is still `"success": true`, with an empty `rows` list and a `row_count` of `0`.



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


## vector_search

Returns the rows whose `VECTOR` column is most similar to a query vector, nearest first, with the distance named and the metric, dimension, element type, and index status reported alongside. This tool requires Analytics Engine 8.0 or later. It is read-only and is available in every `query_mode`.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `table` | `string` | ✓ | Table containing the vector column. Accepts a plain or owner-qualified name. |
| `column` | `string` | ✓ | Unqualified name of the `VECTOR` column to search. |
| `find_like` | `array of number` | ✓ | Query vector. Its length must equal the column's dimension. |
| `metric` | `string` | | `EUCLIDEAN_SQUARED` (default), `EUCLIDEAN`, `COSINE`, `DOT`, `MANHATTAN`, or `HAMMING`. |
| `limit` | `integer` | | Maximum rows to return, from `1` to `200`. Defaults to `10`. |
| `also_return` | `array of string` | | Other columns to return with each row. Defaults to none. |

### Example

**Request**

```
Find the three documents closest to this embedding: [0.12, 0.85, 0.31, 0.40]
```

```json
{
  "table": "documents",
  "column": "embedding",
  "find_like": [0.12, 0.85, 0.31, 0.40],
  "limit": 3,
  "also_return": ["doc_id", "title"]
}
```

For the full output schema, the metrics, index requirements, and an example response, see [Vector Search](../vector-search.md).


## Next Steps

<div class="grid cards" markdown>

- :material-folder-open: **[Resources](../resources/index.md)**  
  Explore the resource types available through the server.

- :material-message-text: **[Prompts](../prompts/index.md)**  
  Use the built-in prompt templates for common workflows.

- :material-vector-point: **[Vector Search](../vector-search.md)**  
  Search `VECTOR` columns by similarity.

</div>