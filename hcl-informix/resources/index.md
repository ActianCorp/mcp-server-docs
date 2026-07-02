---
title: Resources
description: Overview of the resources available when using the Actian MCP Server with HCL Informix® database.
---

# Resources

The Actian MCP Server for HCL Informix® provides a built-in resource that enables comprehensive database schema discovery.


## Available Resources

Use the following resource to retrieve metadata for the database:

| Resource URI | Description |
|--------------|-------------|
| [`resource://database/schema`](#resourcedatabaseschema) | Returns JSON metadata for the connected database, including table names, column definitions, and constraints. |

## resource://database/schema

This resource returns the database schema as a structured JSON object. The response includes details for every user table, such as data types, column lengths, nullability, and key constraints.

### Parameters

This resource does not require any input parameters.

### Output Schema   

**On Success**

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

**Error handling**

If the schema cannot be retrieved, the server returns the following error:

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

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](../tools/index.md)**  
  Learn about the SQL and schema tools provided by the HCL Informix®  server.

- :material-chat-processing: **[Prompts](../prompts/index.md)**  
  Use pre-built prompt templates for common HCL Informix® workflows.

</div>