---
title: Tools
description: Overview of the tools available when using the Actian MCP Server with Actian NoSQL Database.
---

# Tools

The Actian MCP Server for Actian NoSQL registers eight tools for exploring the schema and reading data, and three more for changing it once write mode is on.

!!! note "Response format"
    All tools return results as structured content (`structuredContent`). For compatibility with older MCP clients, each response also includes the same data serialized as a JSON string in a text content item within the `content` array.

    Values that are `null` or absent are omitted from responses entirely, so check whether a key is present rather than whether its value is `null`.

## Available Tools

| Tool | Type | Purpose |
|------|------|---------|
| [`execute_query `](#execute_query) | Read | Runs a read-only JPQL query. |
| [`query_next `](#query_next) | Read | Fetch the next page from a query cursor. |
| [`get_object_by_loid `](#get_object_by_loid) | Read | Fetch one object by LOID. |
| [`get_objects_by_loids `](#get_objects_by_loids) | Read | Fetch multiple objects by LOID. |
| [`count_classes`](#count_classes) | Read | Count database classes. |
| [`list_classes `](#list_classes) | Read | List class names and inheritance. |
| [`describe_class `](#describe_class) | Read | Describe one class in detail. |
| [`get_complete_schema `](#get_complete_schema) | Read | Return full schema for all classes. |
| [`create_objects`](#create_objects) | Write | Create one or more objects of one class. |
| [`update_objects`](#update_objects) | Write | Apply partial field updates to existing objects. |
| [`delete_objects`](#delete_objects) | Write | Delete objects by LOID. |

!!! note "The write tools are not always registered"
    [Write support](../write-support.md) explains whether a client receives the three write tools,
    and what each call must clear before it reaches the database.

    The read tools are not affected by write mode. `execute_query` accepts `SELECT` only, in every
    configuration.

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
| `limit` | `number` | | Maximum number of results to return per page. The server enforces a maximum of **1000** per page. Use the same value in subsequent `query_next` calls for consistent pagination. |

### Output Schema

```json
{
  "items": [          // array of result objects for this page
    {
      "loid": "string",    // the LOID of the object
      "class": "string",   // class name of the object
      "version": "string", // optimistic-concurrency token; pass back as expectedVersion to update
      "fields": {}         // map of field names to their values
    }
  ],
  "count": 0,        // number of items in this page
  "query": "string", // the original JPQL query string
  "pagination": {
    "hasMore": false,       // true if more pages are available
    "cursorId": "string"    // cursor handle for query_next; null when hasMore is false
  }
}
```

A query that selects whole entities (`select e from Employee e`) returns each object in the shape above — the same shape the fetch tools return for the same object. A query that selects individual fields returns those values as they are, not wrapped in `fields`.

To change an object you read here, pass its `version` back as `expectedVersion`. See [Optimistic concurrency](../write-support.md#optimistic-concurrency).

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
      "loid": "135.0.2144",
      "class": "Employee",
      "version": "8273398",
      "fields": {
        "name": "Diana",
        "department": "Executive",
        "annualSalary": 250000,
        "active": true,
        "address": "135.0.2142",
        "accessLevels": [1, 5, 10, 99],
        "subordinates": ["135.0.2145"]
      }
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

| Field | Type | Required | Description                                                                                                                                                                             |
|-------|------|:--------:|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `cursorId` | `string` | ✓ | The cursor ID returned from `execute_query` or a previous `query_next` call.                                                                                                            |
| `limit` | `number` | | Maximum number of results to return per page. The server enforces a maximum of **1000** per page. Use the same value as in the original `execute_query` call for consistent page sizes. |

### Output Schema

The output is identical to `execute_query`:

```json
{
  "items": [          // array of result objects for this page
    {
      "loid": "string",    // the LOID of the object
      "class": "string",   // class name of the object
      "version": "string", // optimistic-concurrency token; pass back as expectedVersion to update
      "fields": {}         // map of field names to their values
    }
  ],
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
      "loid": "135.0.2145",
      "class": "Employee",
      "version": "8273399",
      "fields": {
        "name": "Alice",
        "department": "Engineering",
        "annualSalary": 120000,
        "active": true,
        "address": "135.0.2142"
      }
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
  "data": {              // omitted entirely when found is false
    "loid": "string",    // the LOID of the object
    "class": "string",   // class name of the object
    "version": "string", // optimistic-concurrency token; pass back as expectedVersion to update
    "fields": {}         // map of field names to their values
  }
}
```

To change the object you just read, pass its `version` back as `expectedVersion`. See [Optimistic concurrency](../write-support.md#optimistic-concurrency).

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
    "class": "Employee",
    "version": "8273401",
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
      "class": "string",     // class name of the object
      "version": "string",   // optimistic-concurrency token; pass back as expectedVersion to update
      "fields": {}           // map of field names to their values
    }
  ],
  "count": 0                 // number of objects returned
}
```

LOIDs that match no object are left out of `objects`, so `count` may be lower than the number of LOIDs you asked for. To change any of the objects you read, pass each one's `version` back as `expectedVersion`. See [Optimistic concurrency](../write-support.md#optimistic-concurrency).

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
      "class": "Employee",
      "version": "8273399",
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
      "class": "Employee",
      "version": "8273401",
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
    { "name": "annualSalary", "type": "int" },
    { "name": "department", "type": "java.lang.String" },
    { "name": "subordinates", "type": "java.util.List" },
    "..."
  ],
  "allFields": [
    { "name": "active", "type": "boolean" },
    { "name": "address", "type": "Address {city: java.lang.String; street: java.lang.String; }" },
    { "name": "name", "type": "java.lang.String" },
    { "name": "annualSalary", "type": "int" },
    { "name": "department", "type": "java.lang.String" },
    "..."
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

---

## create_objects

Creates one or more objects of a single class in one atomic transaction. Either every object in the batch is created, or none is.

Available only in write mode, and subject to the checks described in [Write support](../write-support.md).

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `className` | `string` | ✓ | The class to instantiate. Case-sensitive, and must exist in the schema — use [`list_classes`](#list_classes) to check. All objects in one call are of this class. |
| `objects` | `object[]` | ✓ | One field-value map per object. Must contain at least one object, and no more than [`nsql.writes.max-batch`](../write-support.md#configuration-reference). |

A batch over the limit is rejected before anything runs, with a message naming both the size you sent and the maximum this server allows.

### Writable Field Kinds

Field values go in the per-object maps of `create_objects` (`objects[]`) and in `updates[].fields` on `update_objects`. Both accept the same kinds of value, always in the form reads return, so a value read from the database can be written back unchanged.

| Field kind | How to write it |
|------------|-----------------|
| Scalars | Numbers, strings, and booleans, written directly. |
| Dates | Epoch milliseconds (`1700000000000`) or an ISO 8601 string (`"2026-08-10T09:00:00Z"`). |
| Arrays of scalars | A JSON array — `"accessLevels": [1, 5, 10]`. |
| Enums | The **stored** value, because the schema does not surface enums as enums. An ordinal-mapped enum is an integer field: write the ordinal (`1`). A string-mapped enum is a string field: write the constant name (`"NICHES"`). |
| Single references | The target object's LOID string — `"address": "135.0.2142"`. |
| Reference collections | An array of LOID strings — `"subordinates": ["135.0.2145", "135.0.2146"]`. An empty array clears the collection. |
| Maps | An object with exactly the two keys `keys` and `values`, holding equal-length arrays — `"metadata": { "keys": ["role"], "values": ["dev"] }`. No other keys are accepted. Either side may hold LOID strings. |
| Custom references | Not writable. |

!!! warning "Enum values are not validated"
    The server writes the value you supply into the underlying field without checking it against the enum's constants. Writing an out-of-range ordinal stores an out-of-range ordinal. Writing a constant name into an ordinal-mapped integer field fails, because there is no name-to-ordinal conversion.

!!! note "Every referenced object must already exist"
    A reference is resolved when it is written, so objects created in the same call cannot reference each other. Create the referenced objects first, then use the LOIDs the first call returned. The same rule applies to both sides of a reference map.

### Confirmation Prompt

Before the objects are created, the connected client asks the user to approve a summary naming the class and the count:

```text
You are about to create 2 Employee objects.

The objects and their field values were provided in your request.
This action cannot be undone. Confirm?
```

### Output Schema

```json
{
  "className": "string",   // the class of the created objects
  "createdCount": 0,       // how many objects were created
  "createdLoids": ["string"] // LOIDs of the new objects, in input order
}
```

### Example

**User Request**

```
Add Ada and Grace to the Engineering department
```

**Input**

```json
{
  "className": "Employee",
  "objects": [
    {
      "name": "Ada",
      "department": "Engineering",
      "annualSalary": 130000,
      "active": true,
      "address": "135.0.2142"
    },
    {
      "name": "Grace",
      "department": "Engineering",
      "annualSalary": 128000,
      "active": true
    }
  ]
}
```

**Response**

```json
{
  "className": "Employee",
  "createdCount": 2,
  "createdLoids": ["135.0.2148", "135.0.2149"]
}
```

---

## update_objects

Applies partial field updates to existing objects in one atomic transaction. Only the fields you supply are changed; every other field is left as it was. A single call may update objects of different classes.

Available only in write mode, and subject to the checks described in [Write support](../write-support.md).

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `updates` | `object[]` | ✓ | One update per object. Must contain at least one item, and no more than [`nsql.writes.max-batch`](../write-support.md#configuration-reference). |

Each item in `updates` is:

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `loid` | `string` | ✓ | The LOID of the object to change, in dotted format. Each LOID may appear only once per call — combine all changes to one object into a single item. |
| `expectedVersion` | `string` | ✓ | The `version` the object carried when you last read it. See [Optimistic concurrency](../write-support.md#optimistic-concurrency). |
| `fields` | `object` | ✓ | Field name to new value. Must not be empty. Accepts the same values as [`create_objects`](#writable-field-kinds). |

The whole call fails, leaving every object untouched, if any item names a LOID that matches no object, or carries an `expectedVersion` that no longer matches. Re-read the affected objects and retry with the versions you get back.

### Confirmation Prompt

Before the objects are changed, the connected client asks the user to approve a summary. Because one call may span several classes, it gives a count and no class names:

```text
You are about to update 2 existing objects.

The target LOIDs and new field values were provided in your request.
Confirm?
```

### Output Schema

```json
{
  "updatedCount": 0,          // how many objects were updated
  "updatedLoids": ["string"]  // LOIDs of the updated objects, in input order
}
```

### Example

**User Request**

```
Move Bob to the Research department
```

**Input**

```json
{
  "updates": [
    {
      "loid": "135.0.2146",
      "expectedVersion": "8273401",
      "fields": {
        "department": "Research"
      }
    }
  ]
}
```

**Response**

```json
{
  "updatedCount": 1,
  "updatedLoids": ["135.0.2146"]
}
```

**Response when the object changed in the meantime**

The call fails with an error naming the object, the version you sent, and the version it holds now. Nothing is written:

```text
Object [0]: 135.0.2146 was modified since it was read (expected version 8273401,
current 8273402). Re-read the object and retry.
```

Fetch the object again with [`get_object_by_loid`](#get_object_by_loid), take the `version` from that response, and send the update again.

---

## delete_objects

Permanently deletes objects by LOID in one atomic transaction.

Available only in write mode, and subject to the checks described in [Write support](../write-support.md).

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `loids` | `string[]` | ✓ | The LOIDs to delete, in dotted format — for example, `135.0.2148`. Must contain at least one LOID, and no more than [`nsql.writes.max-batch`](../write-support.md#configuration-reference). |

!!! warning "Deletion does not cascade"
    Only the objects you name are removed. Objects that referenced them keep the reference, which now points at nothing. Nothing is rewritten to compensate, and there is no undo — find and fix referencing objects before or after the delete.

### Confirmation Prompt

Before anything is removed, the connected client asks the user to approve a summary. The server looks the LOIDs up first, so the prompt can break the count down by class — ordered by count, then class name — and say how many LOIDs matched nothing:

```text
You are about to permanently delete 2 objects: 1 Address, 1 Employee. 1 requested LOID was not found and will be skipped. This action cannot be undone and does not cascade. Confirm?
```

The not-found sentence appears only when some LOID matched nothing. When *none* of them matches, there is nothing to confirm and no prompt is shown.

### Output Schema

```json
{
  "deletedLoids": ["string"],  // LOIDs that were removed
  "notFoundLoids": ["string"]  // requested LOIDs that matched no object; skipped, not an error
}
```

A LOID that matches no object is a normal outcome, not a failure: it is reported in `notFoundLoids` and the rest of the batch still runs.

### Example

**User Request**

```
Delete the two employee records I imported by mistake
```

**Input**

```json
{
  "loids": ["135.0.2148", "135.0.9999"]
}
```

**Response**

```json
{
  "deletedLoids": ["135.0.2148"],
  "notFoundLoids": ["135.0.9999"]
}
```

## Next Steps

<div class="grid cards" markdown>

- :material-pencil: **[Write support](../write-support.md)**  
  Turn on write mode, and learn the three checks every write passes.

- :material-folder-open: **[Resources](../resources/index.md)**  
  Learn more about schema metadata resources.

- :material-chat-processing: **[Prompts](../prompts/index.md)**  
  Use pre-built prompt templates for common workflows.
  
</div>