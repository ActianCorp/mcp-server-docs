---
title: Resources
description: Overview of the resources available when using the Actian MCP Server with Actian NoSQL Database.
---

# Resources

The Actian MCP Server for Actian NoSQL provides built-in resources that enables comprehensive database schema discovery.

!!! note "Response format"
    Resources return results as text content — the data is serialized as a JSON string in a text content item within the `contents` array. Unlike tools, resources do not use `structuredContent`.

## Available Resources

| Resource URI | Purpose |
|-----|-------------|
| [`db://schema/classes`](#dbschemaclasses) | List all classes and their inheritance hierarchy |
| [`db://schema/classes/count`](#dbschemaclassescount) | Total number of classes in the schema |
| [`db://schema/class/{className}`](#dbschemaclassclassname) | Schema details for a specific class |
| [`db://schema/complete`](#dbschemacomplete) | Complete schema for all classes |

---

## db://schema/classes

Lists all classes in the database schema and their inheritance hierarchy. Returns each class name and its direct parent classes (if any).

### Parameters

This resource takes no input parameters.

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

## db://schema/classes/count

Returns the total number of classes in the database schema.

### Parameters

This resource takes no input parameters.

### Output Schema

```json
{
  "count": 0 // total number of classes
}
```

### Example

```json
{
  "count": 7
}
```

---

## db://schema/class/{className}

Describes the schema of a specific class, including its direct superclasses, declared fields, and all inherited fields. `{className}` is a **URI template parameter** — replace it with the name of the class you want to inspect (for example, `db://schema/class/Employee`).

### Parameters

| Parameter | Description |
|-----------|-------------|
| `className` | The name of the class to describe (case-sensitive). |

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
    { "name": "string", "type": "string" }
  ],
  "allFields": [
    { "name": "string", "type": "string" }
  ]
}
```

### Reading field types

The `type` string tells you whether a field holds a scalar, a reference, or a container.

- **Containers** are `java.util.List<X>`, `java.util.Map<K,V>` and `X[]`. Strip the wrapper to get the element type(s), then read each one by the rules below.
- **Scalars** are Java primitives (`int`, `long`, `short`, `double`, `float`, `boolean`, `byte`, `char`) and any type starting with `java.` — send the value itself. A `long` or `java.math.BigInteger` is the exception: as a **field value** send it as a quoted string, which is also how it is returned. In a JPQL comparison the same number takes a different form — an unquoted literal with an `L` suffix, never a quoted string. See [Large integer literals](../tools/index.md#execute_query).
- **References** are everything else, because any remaining name is a database class. Send the target object's LOID string, never a nested object — `"address": "1.0.5"`, not `"address": { "city": "..." }`.

So `java.util.List<Worker>` holds LOID strings, `java.util.List<java.lang.String>` holds plain strings, and `java.util.Map<java.lang.String,Skill>` has scalar keys and LOID-string values.

!!! warning "A `<` alone does not mean a container"
    Only the `java.util.` prefix does. A class name may itself contain angle brackets — schemas mapped from C++ commonly declare classes such as `BiLink<CsaStudy>` or `CsaPwLinearLUT<o_double,o_double>`. `BiLink<CsaStudy>` is one class name, so a field of that type takes a single LOID, not an array. Use [`db://schema/classes`](#dbschemaclasses) to confirm a name if you need certainty.

See [`create_objects` and `update_objects`](../tools/index.md) for the exact input shape each field kind expects when writing.

### Example

```json
{
  "name": "Employee",
  "superclasses": [
    { "name": "Worker", "superclasses": [] }
  ],
  "declaredFields": [
    { "name": "annualSalary", "type": "int" },
    { "name": "department", "type": "java.lang.String" },
    { "name": "subordinates", "type": "java.util.List<Worker>" },
    { "name": "metadata", "type": "java.util.Map<java.lang.String,java.lang.String>" },
    "..."
  ],
  "allFields": [
    { "name": "active", "type": "boolean" },
    { "name": "address", "type": "Address" },
    { "name": "name", "type": "java.lang.String" },
    { "name": "annualSalary", "type": "int" },
    { "name": "department", "type": "java.lang.String" },
    "..."
  ]
}
```

---

## db://schema/complete

Returns the complete database schema with detailed field information for every class. Each entry includes the class name, direct superclasses, declared fields, and all inherited fields. Prefer this resource when you need a complete picture of the data model upfront, instead of calling `db://schema/classes` followed by multiple `db://schema/class/{className}` reads.

### Parameters

This resource takes no input parameters.

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

- :material-tools: **[Tools](../tools/index.md)**  
  Explore the available MCP tools for NoSQL database operations.

- :material-chat-processing: **[Prompts](../prompts/index.md)**  
  Use pre-built prompt templates for common workflows.

</div>
