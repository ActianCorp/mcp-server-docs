---
title: Tools
description: Overview of the tools available when using the Actian MCP Server with Actian NoSQL Database.
---

# Tools

The Actian MCP Server for **Actian NoSQL Database** exposes a set of tools for document database interaction.

!!! note "Response format"
    All tools return results as **structured content** (`structuredContent`). For compatibility with older MCP clients, each response also includes the same data serialised as a JSON string in the `text` field.

## Available Tools

| Tool | Purpose |
|------|---------|
| [`execute_query `](#execute_query) | Runs a read-only JPQL query. |
| [`query_next `](#query_next) | Fetch the next page from a query cursor. |
| [`get_object_by_loid `](#get_object_by_loid) | Fetch one object by LOID. |
| [`get_objects_by_loids `](#get_objects_by_loids) | Fetch multiple objects by LOID. |
| [`count_classes`](#count_classes) | Count database classes. |
| [`list_classes `](#list_classes) | List class names and inheritance. |
| [`describe_class `](#describe_class) | Describe one class in detail. |
| [`get_complete_schema `](#get_complete_schema) | Return full schema for all classes. |

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

Runs a read-only JPQL query against the connected Actian NoSQL Database and returns the first page of results with pagination metadata. If `pagination.hasMore` is `true`, use `query_next` with the returned `cursorId` to fetch subsequent pages.

!!! note "JPQL limitations"
    The following are **not** supported in this dialect:

    - `JOIN` — use dot notation instead (for example, `p.department.name = 'Engineering'`)
    - Aggregate functions (`COUNT`, `SUM`, `AVG`, etc.)
    - Collection traversal — only single-reference paths are allowed
    - The `in` operator on collections

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `jpql` | `string` | ✓ | JPQL SELECT query to execute. |
| `limit` | `number` | | Maximum number of results to return per page. The server enforces a maximum page size. Use the same value in subsequent `query_next` calls for consistent pagination. |

### Output Schema

```json
{
  "items": [],       // array of result objects for this page
  "count": 0,        // number of items in this page
  "query": "string", // the original JPQL query string
  "pagination": {
    "hasMore": false,       // true if more pages are available
    "cursorId": "string"    // cursor handle for query_next; null when hasMore is false
  }
}
```

### Example

**User Request**

```
Show me all employees
```

**Input**

```json
{
  "jpql": "select e from Employee e"
}
```

**Response**

```json
{
  "items": [
    {
      "name": "Diana",
      "department": "Executive",
      "annualSalary": 250000,
      "active": true,
      "address": "135.0.2142",
      "accessLevels": [1, 5, 10, 99],
      "subordinates": ["135.0.2145"]
    },
    "..."
  ],
  "count": 3,
  "query": "select e from Employee e",
  "pagination": {
    "hasMore": false
  }
}
```

---

## query_next

Fetches the next page of results from a paginated query. Call this tool after `execute_query` returns `pagination.hasMore=true`, passing the `cursorId` from that response. The cursor is automatically closed when exhausted or after a period of inactivity — if it has expired, restart with `execute_query`.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `cursorId` | `string` | ✓ | The cursor ID returned from `execute_query` or a previous `query_next` call. |
| `limit` | `number` | | Maximum number of results to return per page. Use the same value as in the original `execute_query` call for consistent page sizes. |

### Output Schema

The output is identical to `execute_query`:

```json
{
  "items": [],       // array of result objects for this page
  "count": 0,        // number of items in this page
  "query": "string", // the original JPQL query string
  "pagination": {
    "hasMore": false,       // true if more pages are available
    "cursorId": "string"    // cursor handle for the next call; null when hasMore is false
  }
}
```

### Example

**Input**

```json
{
  "cursorId": "f10a7b2b-9532-4280-acdb-fbd41ca7eb35"
}
```

**Response**

```json
{
  "items": [
    {
      "name": "Alice",
      "department": "Engineering",
      "annualSalary": 120000,
      "active": true,
      "address": "135.0.2142"
    },
    "..."
  ],
  "count": 2,
  "query": "select e from Employee e",
  "pagination": {
    "hasMore": false
  }
}
```

---

## get_object_by_loid

Retrieves a single object from the database by its LOID (Logical Object ID). Fetching by LOID is faster than a JPQL query. LOIDs are strings in the format `<classId>.<volumeId>.<objectId>` — for example, `135.0.2146`.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `loid` | `string` | ✓ | The LOID of the object to retrieve. |

### Output Schema

```json
{
  "found": true,         // true if the object was found, false otherwise
  "data": {
    "loid": "string",    // the LOID of the object
    "className": "string", // class name of the object
    "fields": {}         // map of field names to their values
  }
}
```

### Example

**Input**

```json
{
  "loid": "135.0.2146"
}
```

**Response**

```json
{
  "found": true,
  "data": {
    "loid": "135.0.2146",
    "className": "Employee",
    "fields": {
      "name": "Bob",
      "department": "Engineering",
      "annualSalary": 90000,
      "active": true,
      "address": "135.0.2143",
      "skills": ["135.0.2138", "135.0.2136"],
      "technicalTags": ["Backend", "API"]
    }
  }
}
```

---

## get_objects_by_loids

Retrieves multiple objects from the database by their LOIDs (Logical Object IDs) in a single call. Fetching by LOID is faster than a JPQL query.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `loids` | `string[]` | ✓ | Array of LOIDs to retrieve. Each LOID is a string in the format `<classId>.<volumeId>.<objectId>` — for example, `135.0.2145`. |

### Output Schema

```json
{
  "objects": [
    {
      "loid": "string",      // the LOID of the object
      "className": "string", // class name of the object
      "fields": {}           // map of field names to their values
    }
  ],
  "count": 0                 // number of objects returned
}
```

### Example

**Input**

```json
{
  "loids": ["135.0.2145", "135.0.2146"]
}
```

**Response**

```json
{
  "objects": [
    {
      "loid": "135.0.2145",
      "className": "Employee",
      "fields": {
        "name": "Alice",
        "department": "Engineering",
        "annualSalary": 120000,
        "active": true,
        "address": "135.0.2142",
        "subordinates": ["135.0.2146", "135.0.2147"]
      }
    },
    {
      "loid": "135.0.2146",
      "className": "Employee",
      "fields": {
        "name": "Bob",
        "department": "Engineering",
        "annualSalary": 90000,
        "active": true,
        "address": "135.0.2143",
        "technicalTags": ["Backend", "API"]
      }
    }
  ],
  "count": 2
}
```

---

## count_classes

Returns the total number of classes in the database schema.

### Parameters

This tool takes no input parameters.

### Output Schema

```json
{
  "count": 0 // total number of classes
}
```

### Example

**Response**

```json
{
  "count": 7
}
```

---

## list_classes

Lists all classes in the database schema and their inheritance hierarchy. Returns each class name and its direct parent classes (if any). Use this to discover available classes before querying or describing specific ones.

### Parameters

This tool takes no input parameters.

### Output Schema

```json
{
  "classes": [
    {
      "name": "string",           // class name
      "superclasses": ["string"]  // list of direct parent class names; empty if none
    }
  ],
  "count": 0                      // total number of classes
}
```

### Example

**Response**

```json
{
  "classes": [
    { "name": "Project", "superclasses": [] },
    { "name": "Skill", "superclasses": [] },
    { "name": "Employee", "superclasses": ["Worker"] },
    { "name": "Contractor", "superclasses": ["Worker"] },
    { "name": "Address", "superclasses": [] },
    { "name": "Worker", "superclasses": [] },
    { "name": "Certificate", "superclasses": [] }
  ],
  "count": 7
}
```

---

## describe_class

Describes the schema of a specific class, including its direct superclasses, declared fields, and all inherited fields. Use this after `list_classes` to understand the structure of a specific entity before querying it.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `className` | `string` | ✓ | The name of the class to describe (case-sensitive). |

### Output Schema

```json
{
  "name": "string",               // class name
  "superclasses": [
    {
      "name": "string",           // direct parent class name
      "superclasses": ["string"]  // parent's own direct parents; empty if none
    }
  ],
  "declaredFields": [
    {
      "name": "string",           // field name
      "type": "string"            // field type
    }
  ],
  "allFields": [
    {
      "name": "string",           // field name (declared or inherited)
      "type": "string"            // field type
    }
  ]
}
```

### Example

**Input**

```json
{
  "className": "Employee"
}
```

**Response**

```json
{
  "name": "Employee",
  "superclasses": [
    { "name": "Worker", "superclasses": [] }
  ],
  "declaredFields": [
    { "name": "accessLevels", "type": "int[]" },
    { "name": "annualSalary", "type": "int" },
    { "name": "department", "type": "java.lang.String" },
    { "name": "metadata", "type": "java.util.Map" },
    { "name": "performanceBonus", "type": "double" },
    { "name": "skillMap", "type": "java.util.Map" },
    { "name": "subordinates", "type": "java.util.List" },
    { "name": "technicalTags", "type": "java.util.List" }
  ],
  "allFields": [
    { "name": "active", "type": "boolean" },
    { "name": "address", "type": "Address {city: java.lang.String; street: java.lang.String; }" },
    { "name": "certifications", "type": "java.util.List" },
    { "name": "lastLogin", "type": "java.sql.Timestamp" },
    { "name": "name", "type": "java.lang.String" },
    { "name": "projects", "type": "java.util.List" },
    { "name": "skills", "type": "java.util.List" },
    { "name": "startDate", "type": "java.sql.Timestamp" },
    { "name": "accessLevels", "type": "int[]" },
    { "name": "annualSalary", "type": "int" },
    { "name": "department", "type": "java.lang.String" },
    { "name": "metadata", "type": "java.util.Map" },
    { "name": "performanceBonus", "type": "double" },
    { "name": "skillMap", "type": "java.util.Map" },
    { "name": "subordinates", "type": "java.util.List" },
    { "name": "technicalTags", "type": "java.util.List" }
  ]
}
```

---

## get_complete_schema

Returns the complete database schema with detailed field information for every class. Each entry includes the class name, direct superclasses, declared fields, and all inherited fields. Prefer this tool when you need a complete picture of the data model upfront, instead of calling `list_classes` followed by multiple `describe_class` calls.

### Parameters

This tool takes no input parameters.

### Output Schema

```json
{
  "classes": [
    {
      "name": "string",               // class name
      "superclasses": [
        {
          "name": "string",           // direct parent class name
          "superclasses": ["string"]  // parent's own direct parents; empty if none
        }
      ],
      "declaredFields": [
        { "name": "string", "type": "string" }
      ],
      "allFields": [
        { "name": "string", "type": "string" }
      ]
    }
  ],
  "count": 0                          // total number of classes
}
```

### Example

**Response**

```json
{
  "classes": [
    {
      "name": "Project",
      "superclasses": [],
      "declaredFields": [
        { "name": "budget", "type": "int" },
        { "name": "projectName", "type": "java.lang.String" }
      ],
      "allFields": [
        { "name": "budget", "type": "int" },
        { "name": "projectName", "type": "java.lang.String" }
      ]
    },
    {
      "name": "Employee",
      "superclasses": [{ "name": "Worker", "superclasses": [] }],
      "declaredFields": [
        { "name": "annualSalary", "type": "int" },
        { "name": "department", "type": "java.lang.String" }
      ],
      "allFields": [
        { "name": "active", "type": "boolean" },
        { "name": "name", "type": "java.lang.String" },
        { "name": "annualSalary", "type": "int" },
        { "name": "department", "type": "java.lang.String" }
      ]
    },
    {
      "name": "Worker",
      "superclasses": [],
      "declaredFields": [
        { "name": "active", "type": "boolean" },
        { "name": "name", "type": "java.lang.String" }
      ],
      "allFields": [
        { "name": "active", "type": "boolean" },
        { "name": "name", "type": "java.lang.String" }
      ]
    },
    "..."
  ],
  "count": 7
}
```

## Next Steps

<div class="grid cards" markdown>

- :material-folder-open: **[Resources](../resources/index.md)**  
  Explore the resource types available through the NoSQL server.

- :material-chat-processing: **[Prompts](../prompts/index.md)**  
  Discover pre-built prompt templates for common NoSQL workflows.
  
</div>