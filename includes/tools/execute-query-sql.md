Use this tool to run a SQL query against Actian Ingres. The server returns the result set as structured `JSON`.

By default the tool accepts only `SELECT`. When the server runs with `query_mode` set to `read-write`, it also accepts the Data Manipulation Language (DML) statements `INSERT`, `UPDATE`, and `DELETE`. See [Write support](../../intro/write-support.md).

!!! note "Result truncation:"
    If the number of rows exceeds the `max_rows` configuration, the response includes the `truncated` and `warning` fields.

!!! warning "Data Definition Language is never permitted"
    This tool does not run Data Definition Language (DDL) or administrative statements in any mode. `CREATE`, `ALTER`, `DROP`, `GRANT`, `SET`, `ENABLE`, `DISABLE`, and `SELECT ... INTO` are rejected. Use Ingres tooling for schema changes.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `query` | `string` | ✓ | The SQL query you want to execute. `SELECT` is always accepted. `INSERT`, `UPDATE`, and `DELETE` require `query_mode` set to `read-write`. |

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
  "row_count": "<num_rows>"
}
```
