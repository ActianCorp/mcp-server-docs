---
title: Resources
description: Overview of the resources available when using the Actian MCP Server with Informix database.
---

# Resources

The Actian MCP Server for **Informix database** exposes a built-in resource for database schema discovery.

## Available resources

The Informix database integration provides the following resource:

| Resource URI | Purpose |
|-----|-------------|
| `resource://database/schema` | Returns database schema metadata for the connected database. |

## resource://database/schema

### Description

Returns the database schema as JSON, including tables, columns, comments, and constraint information.

### Input Parameters

This resource doesn't require any input parameters.

### Output Schema

```json
{
    "<table_name>": {
        "columns": {
            "<column_name>": {
                "dtype": "<column_datatype>",
                "length": "<column_length>",
                "nullable": "<NULL value>",
                "key": "<Constraint type>"
            }
        }
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
     "customers":
        {
            "columns": {"email": {"dtype": "VARCHAR(50)", "length": "50", "nullable": "NOT NULL", "key": "None"},
                        "customer_id": {"dtype": "INTEGER", "length": "4", "nullable": "NULL    ", "key": "P   "}},
        },
        "orders":
        {
            "columns": {"order_id": {"dtype": "INTEGER", "length": "4", "nullable": "NOT NULL", "key": "None"},
                        "order_date": {"dtype": "DATE", "length": "4", "nullable": "NOT NULL", "key": "None"},
                        "customer_id": {"dtype": "INTEGER", "length": "4", "nullable": "NOT NULL", "key": "None"},
                        "total_amount": {"dtype": "MONEY", "length": "4098", "nullable": "NOT NULL", "key": "None"}},
        }
}
```

## Next steps

- [Tools](../tools/index.md) — Learn about Informix MCP server tools
- [Prompts](../prompts/index.md) — Learn about Informix MCP server prompts