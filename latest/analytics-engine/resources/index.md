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
| [`resource://database/{host}/{instance}/{database}/schema`](#multi-target-deployments) | In a multi-target deployment, the schema of one target database. Same output as `resource://database/schema`. |
| [`targets://accessible`](#targetsaccessible) | In a multi-target deployment, the databases the caller can read. |


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

### Vector Columns

On Analytics Engine 8.0 and later, the `dtype` of a `VECTOR` column is its full declaration: the dimension followed by the element type. Examples are `VECTOR(4, FLOAT4)`, `VECTOR(2, INTEGER)`, and `VECTOR(3, DECIMAL(5,2))`. If the server cannot read the dimension or element type from the catalog, `dtype` is `VECTOR`.

```json
{
  "documents": {
    "columns": {
      "doc_id": {
        "dtype": "INTEGER",
        "comment": null
      },
      "embedding": {
        "dtype": "VECTOR(4, FLOAT4)",
        "comment": "Text embedding"
      }
    },
    "keys": ["PRIMARY KEY (doc_id)"],
    "comment": null
  }
}
```

The example data is illustrative. To search a vector column, see [Vector Search](../vector-search.md).

---

## Multi-Target Deployments

In a [multi-target deployment](../multi-target.md), each database has its own schema resource, named after the target's URL segments:

```text
resource://database/{host}/{instance}/{database}/schema
```

For example, `resource://database/sales-db.example.com/VW/salesmart/schema`. The output is the same as for `resource://database/schema`.

- A session connected to a target's URL lists only that target's schema resource.
- Reading another target's schema URI over that session returns "resource not found", the same as a URI that does not exist.
- After targets are added or removed through `targets.d/`, list resources again to see the change.

## targets://accessible

In a multi-target deployment, this resource returns the databases the caller's token can read, with the URL path to connect to each one. It returns the same data as the `list_accessible_targets` tool. For the output format, see [Discover Which Databases You Can Reach](../multi-target.md#discover-which-databases-you-can-reach).

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](../tools/index.md)**  
  Learn more about the SQL and schema tools provided by the Analytics Engine server.

- :material-message-text: **[Prompts](../prompts/index.md)**  
  Use the built-in prompt templates for common workflows.

</div>