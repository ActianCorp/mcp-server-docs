---
title: Resources
description: Overview of the resources available when using the Actian MCP Server with HCL Informix® database.
---

# Resources

The Actian MCP Server for **HCL Informix® database** exposes a built-in resource for database schema discovery.

## Available resources

| Resource URI | Description |
|--------------|-------------|
| [`resource://database/schema`](#resourcedatabaseschema) | Returns database schema metadata for the connected database. |

## resource://database/schema

Returns the database schema as JSON, including tables, columns, comments, and constraint information.

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
                "length": "<column_length>",
                "nullable": "<NULL value>",
                "key": "<Constraint type>"
            }
        }
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

<div class="grid cards" markdown>

- :material-tools: **[Tools](../tools/index.md)**  
  Learn about the SQL and schema tools exposed by the HCL Informix® server.

- :material-chat-processing: **[Prompts](../prompts/index.md)**  
  Discover pre-built prompt templates for common HCL Informix® workflows.

</div>