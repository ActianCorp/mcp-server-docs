Returns user-defined functions and procedures, including their stored definitions, as structured JSON.

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
  "row_count": "<num_rows>"
}
```
