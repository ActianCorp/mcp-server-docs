---
title: Resources
description: Built-in resources available when using the Actian MCP Server with Actian Analytics Engine.
---

# Resources

The Actian MCP Server for **Actian Analytics Engine** provides a built-in resource that returns live schema metadata for the connected database.


## Available resources

| Resource URI | Description |
|--------------|-------------|
| [`resource://database/schema`](#resourcedatabaseschema) | Returns schema metadata including tables, columns, constraints, and comments. |


## resource://database/schema

Fetches the full database schema as a structured JSON object. Use this resource to inspect table and column definitions before writing queries.

### Parameters

This resource takes no input parameters.

### Output schema

**On success**

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

**On error**

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

## Next steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](../tools/index.md)**  
  Learn about the SQL and schema tools exposed by the Analytics Engine server.

- :material-message-text: **[Prompts](../prompts/index.md)**  
  Review the built-in prompt templates for common workflows.

</div>