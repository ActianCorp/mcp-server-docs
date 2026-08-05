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
  "row_count": "<num_rows>"
}
```

**Error Response**

```json
{
  "success": false,
  "error": "No permission to access table 'customers'"
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
