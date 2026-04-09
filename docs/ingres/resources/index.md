---
title: Resources
description: Overview of the resources available when using the Actian MCP Server with Actian Ingres.
---

# Resources

The Actian MCP Server for **Actian Ingres** exposes a built-in resource for database schema discovery.

## Available Resources

| Resource URI | Description |
|--------------|-------------|
| [`resource://database/schema`](#resourcedatabaseschema) | Returns database schema metadata for the connected database. |

## resource://database/schema

Returns the database schema as JSON, including tables, columns, comments, and constraint information.

### Parameters

This resource takes no input parameters.

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

**On Error**

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
        "keys": [
            "PRIMARY KEY (customer_id)"
        ],
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
        "keys": [
            "PRIMARY KEY (order_id)"
        ],
        "comment": "Sales orders"
    }
}
```

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](../tools/index.md)**  
  Learn about the SQL and schema tools exposed by the Ingres server.

- :material-chat-processing: **[Prompts](../prompts/index.md)**  
  Discover pre-built prompt templates for common Ingres workflows.

</div>
