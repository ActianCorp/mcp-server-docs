---
title: Resources
description: Built-in resources available when using the Actian MCP Server with Actian Analytics Engine.
---

# Resources

The Actian MCP Server for the Actian Analytics Engine includes a built-in resource for exploring live schema metadata. This resource is particularly useful for providing context to an LLM, ensuring it understands the table relationships and data types of the specific environment.


## Available Resources

| Resource URI | Description |
|--------------|-------------|
| [`resource://database/schema`](#resourcedatabaseschema) | Retrieves metadata for the connected database, including tables, columns, and constraints. |


## resource://database/schema

Use the `resource://database/schema` URI to fetch the full database schema as a structured JSON object. You can use resource to inspect table and column definitions before you write or execute SQL queries.


### Parameters

This resource does not require input parameters.

### Output Schema

**On Success**

```json
{
  "<table_name>": {
    "columns": {
      "<column_name>": {
        "dtype": "<column_datatype>",
        "comment": "<column_comment>"
      }
    },
    "keys": ["<constraint_definition>"],
    "comment": "<table_comment>"
  }
}
```

**Error handling**

If the schema cannot be retrieved, the server returns an error message:

```text
The database schema could not be retrieved. Error: <error_message>
```

### Example

**Request**

```text
resource://database/schema
```

**Response**

```json
{
  "customers": {
    "columns": {
      "customer_id": {
        "dtype": "integer",
        "comment": "Primary key"
      },
      "customer_name": {
        "dtype": "varchar",
        "comment": "Customer display name"
      }
    },
    "keys": ["PRIMARY KEY (customer_id)"],
    "comment": "Customer master data"
  },
  "orders": {
    "columns": {
      "order_id": {
        "dtype": "integer",
        "comment": "Primary key"
      },
      "customer_id": {
        "dtype": "integer",
        "comment": "Customer reference"
      }
    },
    "keys": ["PRIMARY KEY (order_id)"],
    "comment": "Sales orders"
  }
}
```

---

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](../tools/index.md)**  
  Learn more about the SQL and schema tools provided by the Analytics Engine server.

- :material-message-text: **[Prompts](../prompts/index.md)**  
  Use the built-in prompt templates for common workflows.

</div>