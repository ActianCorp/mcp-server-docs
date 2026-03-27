---
title: Resources
description: Overview of the resources available when using the Actian MCP Server with Actian Analytics Engine.
---

# Resources

The Actian MCP Server for **Actian Analytics Engine** exposes a built-in resource for database schema discovery.

---

## Available Resources

The Analytics Engine integration provides the following resource:

| Resource URI | Purpose |
|-----|-------------|
| `resource://database/schema` | Return database schema metadata for the connected database |

---

## resource://database/schema

### Description

Returns the database schema as JSON, including tables, columns, comments, and constraint information.

### Input Parameters

This resource does not require any input parameters.

### Output Schema

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

On error:

```text
The database schema could not be retrieved. Error: <error_message>
```

### Example

```text
resource://database/schema
```

### Success Response Example

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

---

## Next Steps
- [Tools](../tools/index.md) — Learn about Analytics Engine tools
- [Prompts](../prompts/index.md) — Learn about Analytics Engine prompts
