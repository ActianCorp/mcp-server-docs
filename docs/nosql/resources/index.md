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
