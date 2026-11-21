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
| [`resource://database/{host}/{instance}/{database}/schema`](#multi-target-deployments) | In a multi-target deployment, the schema of one target database. Same output as `resource://database/schema`. |
| [`targets://accessible`](#targetsaccessible) | In a multi-target deployment, the databases the caller can read. |

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
## Multi-Target Deployments

In a [multi-target deployment](../multi-target.md), each database has its own schema resource, named after the target's URL segments:

```text
resource://database/{host}/{instance}/{database}/schema
```

For example, `resource://database/sales-db.example.com/II/salesmart/schema`. The output is the same as for `resource://database/schema`.

- A session connected to a target's URL lists only that target's schema resource.
- Reading another target's schema URI over that session returns "resource not found", the same as a URI that does not exist.
- After targets are added or removed through `targets.d/`, list resources again to see the change.

## targets://accessible

In a multi-target deployment, this resource returns the databases the caller's token can read, with the URL path to connect to each one. It returns the same data as the `list_accessible_targets` tool. For the output format, see [Discover Which Databases You Can Reach](../multi-target.md#discover-which-databases-you-can-reach).

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](../tools/index.md)**  
  Learn about the SQL and schema tools provided by the HCL Informix®  server.

- :material-chat-processing: **[Prompts](../prompts/index.md)**  
  Use pre-built prompt templates for common HCL Informix® workflows.

</div>