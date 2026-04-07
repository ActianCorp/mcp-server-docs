---
title: Tools
description: Overview of the tools available when using the Actian MCP Server with Actian NoSQL Database.
---

# Tools

The Actian MCP Server for **Actian NoSQL Database** exposes a set of tools for document database interaction.

## Available tools

| Tool | Purpose |
|------|---------|
| `execute_query ` | run a JPQL query |
| `query_next ` | fetch the next page from a query cursor |
| `get_object_by_loid ` | fetch one object by LOID |
| `get_objects_by_loids ` | fetch multiple objects by LOID |
| `count_classes` | count database classes |
| `list_classes ` | list class names and inheritance |
| `describe_class ` | describe one class in detail |
| `get_complete_schema ` | return full schema for all classes |

<!-- 
### Write tools (full mode only)

| Tool | Purpose |
|------|---------|
| `insert_document` | Insert a document into a collection. |
| `update_document` | Update an existing document. |
| `delete_document` | Delete a document from a collection. |

-->

---

## execute_query

### Description

Use execute_query to start any database query from the MCP server.

It returns:

	•  the first page of results
	•  paging metadata
	•  a cursor id if more results are available

If the response says there are more results, you continue with query_next using the returned cursor.

### When to use it

Use execute_query when:

	•  you want to search objects by field values
	•  you want a filtered set of entities
	•  you don’t already know the target object LOIDs
	•  you want to inspect a subset of data before fetching more pages

Prefer the LOID fetch tools instead when:

	•  you already know the object LOID(s)
	•  you want the fastest direct retrieval path


### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `jpql` | `string` | Yes | The JPQL SELECT query to execute. |
| `limit` | `number` | No | Maximum number of items to return in the first page. |


### Output Schema

```json
{
	"items": [ /*array of objects, each representing a result item*/ ],
	"count": 0, // integer: number of items in this page
	"query": "string", // the original JPQL query string
	"pagination":
	{
		"hasMore": false, // boolean: whether more items exist beyond this page
		"cursorId": "string or null" // string: opaque cursor handle for query_next, or null if hasMore is false
	}
}
```

### Example

Show me all cars with the plate containing “123”

```json
{
	“jpql”: "select c from Car c where c.plate like '%123%'"
}
```

### Success Response Example

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "result": {
    "isError": false,
    "structuredContent": {
      "items": [
        {
          "plate": "1234",
          "thing": "54.0.22538",
          "vehicle": "54.0.22539"
        }
      ],
      "count": 1,
      "query": "select c from Car c where c.plate like '%123%'",
      "pagination": {
        "hasMore": false
      }
    }
  }
}
```

---

## query_next

### Description

The query_next tool is used to retrieve the next page of results from a paginated JPQL query. When you execute a query with execute_query and the response indicates that more results are available (pagination.hasMore is true), you use query_next with the provided cursorId to fetch subsequent pages.

### Usage	

	1. Run execute_query with your JPQL query.
	2. If the response contains "pagination.hasMore": true, note the "cursorId".
	3. Call query_next with that cursorId to get the next page of results.
	4. Repeat until "pagination.hasMore" is false.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `cursorId` | `string` | Yes | The cursor ID returned from execute_query or a previous query_next call. |
| `limit` | `number` | No | Maximum number of items to return in the first page. |

### Response Schema

The response from query_next is identical to execute_query:

```json
{
	"items": [ /*array of objects, each representing a result item*/ ],
	"count": 0, // integer: number of items in this page
	"query": "string", // the original JPQL query string
	"pagination":
	{
		"hasMore": false, // boolean: whether more items exist beyond this page
		"cursorId": "string or null" // string: opaque cursor handle for query_next, or null if hasMore is false
	}
}
```

---

## get_object_by_loid

### Description

The get_object_by_loid tool retrieves a single object from the database using its LOID (Logical Object ID). This is the fastest way to fetch a specific instance when you already know its LOID.

### When to use
Use this tool when you need to fetch details for a specific object and you already have its LOID. For multiple objects, use get_objects_by_loids.

Usage Steps:

	1. Obtain the LOID of the object you want (e.g., from a previous query).
	2. Call get_object_by_loid with the LOID as a parameter.
	3. The tool returns the full object data for that LOID.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `loid` | `string` | Yes | The LOID of the instance in dotted string format (e.g., "15.0.2085") |

### Response Schema

```json
{
  "found": true,                // boolean: true if the object was found, false otherwise
  "data": {                     // object: the fetched object data, or null if not found
    "loid": "string",           // string: Logical Object ID (e.g., "15.0.2085")
    "className": "string",      // string: class name of the object
    "fields": {                 // object: map of field names to their values
      "field1": "value1",
      "field2": "value2"
      // ... more fields ...
    }
  }
}
```

### Example

Get the object with id 54.0.22538

```json
{
  "loid": "54.0.22538"
}
```

### Success Response Example

```json
{
  "jsonrpc": "2.0",
  "id": 9,
  "result": {
    "isError": false,
    "structuredContent": {
      "found": true,
      "data": {
        "loid": "54.0.22538",
        "className": "Vehicle",
        "fields": {
          "plate": "1234"
        }
      }
    }
  }
}
```

---

## get_objects_by_loid

### Description

The get_objects_by_loid tool retrieves multiple objects from the database using their LOIDs (Logical Object ID). This is the fastest way to fetch a specific instances when you already know their LOIDs.

### When to use
Use this tool when you need to fetch details for specific objects and you already have their LOIDs.

Usage Steps:

	1. Obtain the LOIDs of the objects you want to fetch (e.g., from a previous query).
	2. Call get_objects_by_loid with the LOIDs as a parameter.
	3. The tool returns the full object data for these LOIDs.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `loids` | `string[]` | Yes | An array of LOIDs for the instances to be fetched in dotted string format (e.g., "15.0.2085") |

### Response Schema

```json
{
  "objects": [
    {
      "loid": "string",         // Logical Object ID (e.g., "15.0.2085")
      "className": "string",    // Class name of the object
      "fields": {               // Map of field names to their values
        "field1": "value1",
        "field2": "value2"
        // ... more fields ...
      }
    }
    // ... more objects ...
  ],
  "count": 0                   // Number of objects returned (integer)
}
```

### Example

Get the objects with id 54.0.22537, 54.0.22538

```json
{
  "loids": [
    "54.0.22537",
    "54.0.22539"
  ]
}
```

### Success Response Example


```json
{
  "jsonrpc": "2.0",
  "id": 33,
  "result": {
    "isError": false,
    "structuredContent": {
      "objects": [
        {
          "loid": "54.0.22537",
          "className": "Car",
          "fields": {
            "plate": "1234",
            "thing": "54.0.22538",
            "vehicle": "54.0.22539"
          }
        },
        {
          "loid": "54.0.22539",
          "className": "Vehicle",
          "fields": {
            "plate": "1234"
          }
        }
      ],
      "count": 2
    }
  }
}
```

---

## count_classes

### Description

The count_classes tool returns the total number of classes (entity types) defined in the database schema. It provides a single integer value representing how many distinct classes are available for querying or object retrieval. This is useful for schema introspection and understanding the data model's complexity.

### Input Parameters

This tool does not use any input parameters.

### Output Schema

```json
{
  "count": 0 // integer: the total number of classes in the database schema
}

```

### Example

```json
{}
```

### Success Response Example

```json
{
  "jsonrpc": "2.0",
  "id": 36,
  "result": {
    "isError": false,
    "structuredContent": {
      "count": 3
    }
  }
}
```

---

## list_classes

### Description

The list_classes tool returns a list of all classes (entity types) defined in the database schema, along with their names and superclasses. This is useful for discovering the available data model structure and understanding class inheritance relationships.

### Input Parameters

This tool does not use any input parameters.

### Output Schema

```json
{
  "classes": [
    {
      "name": "string",         // Name of the class (entity type)
      "superclass": "string"    // Name of the superclass (or null if none)
    }
    // ... more classes ...
  ],
  "count": 0                   // Total number of classes (integer)
}
```

### Example

```json
{}
```

### Success Response Example

```json
{
  "jsonrpc": "2.0",
  "id": 37,
  "result": {
    "isError": false,
    "structuredContent": {
      "classes": [
        {
          "name": "Vehicle",
          "superclass": "Thing"
        },
        {
          "name": "Car",
          "superclass": "Vehicle"
        },
        {
          "name": "Thing"
        }
      ],
      "count": 3
    }
  }
}
```

---

## describe_class

### Description

The describe_class tool provides a detailed description of a specific class in the **Actian NoSQL Database** schema. Its main purpose is to return the schema metadata for a given class, including:

	•  The class name and its superclass (if any)
	•  All declared fields (attributes) of the class
	•  All inherited fields from parent classes
	•  Field types, names, and possibly additional metadata (such as whether a field is a reference, collection, etc.)

This tool is typically used to programmatically discover the structure of entities in the database, which is essential for dynamic clients, schema introspection, or building generic UI/data tools.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `className` | `string` | Yes | The name of the class to describe (case-sensitive) |

### Output Schema

```json
{
	"className": "string", // Name of the class (entity)
	"superClassName": "string|null", // Name of the superclass, or null if none
	"fields": [ 
		{
			"name": "string", // Field name
			"type": "string", // Field type (e.g., "String", "Integer", "Date", "Reference", etc.)
			"reference": "boolean", // True if the field is a reference to another class
			"collection": "boolean", // True if the field is a collection (list/set)
			"declaredIn": "string", // Name of the class where the field is declared
			"nullable": "boolean", // True if the field can be null
			"description": "string|null" // Optional field description or comment
			// ...other metadata as needed
		 }
		// ...more fields
	]
 }
```

### Example

```json
{
  "className": "Vehicle"
}
```

### Success Response Example

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "isError": false,
    "structuredContent": {
      "name": "Vehicle",
      "superclass": {
        "name": "Thing"
      },
      "declaredFields": [
        {
          "name": "plate",
          "type": "java.lang.String"
        }
      ],
      "allFields": [
        {
          "name": "plate",
          "type": "java.lang.String"
        }
      ]
    }
  }
}
```

---

## get_complete_schema

### Description

The get_complete_schema returns the entire database schema for the  connected **Actian NoSQL Database**. It provides detailed metadata for every class in the schema, including class names, superclasses, and all declared and inherited fields with their types and properties.

This tool is useful for clients or tools that need to understand the full data model in a single call, enabling dynamic UI generation, schema introspection, or code generation.

### Input Parameters

This tool does not use any input parameters.

### Output Schema

```json
{
	"classes": [
	{
		"className": "string", // Name of the class (entity)
		"superClassName": "string|null", // Name of the superclass, or null if none
		"fields": [
		{
			"name": "string", // Field name
			"type": "string", // Field type (e.g., "String", "Integer", "Date", "Reference", etc.)
			"reference": "boolean", // True if the field is a reference to another class
			"collection": "boolean", // True if the field is a collection (list/set)
			"declaredIn": "string", // Name of the class where the field is declared
			"nullable": "boolean", // True if the field can be null
			"description": "string|null" // Optional field description or comment
			// ...other metadata as needed
		}
		// ...more fields
		]
	} 
	// ...more classes
	]
}
```

Explanation:

	•  The top-level object contains a "classes" array.
	•  Each entry in "classes" describes a single class/entity in the schema.
	•  Each class includes its name, optional superclass, and a list of all fields (including inherited ones).
	•  	Each field object provides its name, type, reference/collection status, where it was declared, nullability, and an optional description.

### Example

```json
{}
```

### Success Response Example

```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "result": {
    "isError": false,
    "structuredContent": {
      "classes": [
        {
          "name": "Vehicle",
          "superclass": {
            "name": "Thing"
          },
          "declaredFields": [
            {
              "name": "plate",
              "type": "java.lang.String"
            }
          ],
          "allFields": [
            {
              "name": "plate",
              "type": "java.lang.String"
            }
          ]
        },
        {
          "name": "Car",
          "superclass": {
            "name": "Vehicle",
            "superclass": "Thing"
          },
          "declaredFields": [
            {
              "name": "somethingElse",
              "type": "Thing {}"
            },
            {
              "name": "trailer",
              "type": "Vehicle extends Thing {plate: java.lang.String; }"
            }
          ],
          "allFields": [
            {
              "name": "plate",
              "type": "java.lang.String"
            },
            {
              "name": "somethingElse",
              "type": "Thing {}"
            },
            {
              "name": "trailer",
              "type": "Vehicle extends Thing {plate: java.lang.String; }"
            }
          ]
        },
        {
          "name": "Thing",
          "declaredFields": [],
          "allFields": []
        }
      ],
      "count": 3
    }
  }
}
```

