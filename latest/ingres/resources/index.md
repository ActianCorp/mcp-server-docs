---
title: Resources
description: Overview of the resources available when using the Actian MCP Server with Actian Ingres.
---

# Resources

The Actian MCP Server for Actian Ingres provides a built-in resource that helps to discover and understand your database schema.

## Available Resources

The following resource is available for schema discovery:

| Resource URI | Description |
|--------------|-------------|
| [`resource://database/schema`](#resourcedatabaseschema) | Returns metadata for the connected database, including tables, columns, and constraints. |
| [`resource://database/{host}/{instance}/{database}/schema`](#multi-target-deployments) | In a multi-target deployment, the schema of one target database. Same output as `resource://database/schema`. |
| [`targets://accessible`](#targetsaccessible) | In a multi-target deployment, the databases the caller can read. |

## resource://database/schema

Use this resource to retrieve a comprehensive view of the database structure in JSON format. The output includes column definitions, data types, comments, and constraint information.

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

The server returns a nested JSON object where each top-level key is a table name.

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
  Learn about the SQL and schema tools provided by the MCP Server for Ingres.

- :material-chat-processing: **[Prompts](../prompts/index.md)**  
  Use pre-built prompt templates for common Ingres workflows.

</div>
