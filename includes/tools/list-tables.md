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

**User Request**

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
  "row_count": "<num_rows>"
}
```
