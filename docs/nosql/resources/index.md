---
title: Resources
description: Overview of the resources available when using the Actian MCP Server with Actian NoSQL Database.
---

# Resources

The Actian MCP Server for **Actian NoSQL Database** exposes built-in resources for data discovery.

## Available Resources

| Resource URI | Purpose |
|-----|-------------|
| [`db://schema/classes`](#dbschemaclasses) | List all classes and their inheritance hierarchy |
| [`db://schema/classes/count`](#dbschemaclassescount) | Total number of classes in the schema |
| [`db://schema/class/{className}`](#dbschemaclassclassname) | Schema details for a specific class |
| [`db://schema/complete`](#dbschemacomplete) | Complete schema for all classes |

---

## db://schema/classes

Lists all classes in the database schema and their inheritance hierarchy. Returns each class name and its parent class (if any).

### Output Schema

```json
{
  "classes": [
    {
      "name": "string",       // class name
      "superclass": "string"  // parent class name; omitted if none
    }
  ],
  "count": 0                  // total number of classes
}
```

### Example

```json
{
  "classes": [
    { "name": "Project" },
    { "name": "Skill" },
    { "name": "Employee", "superclass": "Worker" },
    { "name": "Contractor", "superclass": "Worker" },
    { "name": "Address" },
    { "name": "Worker" },
    { "name": "Certificate" }
  ],
  "count": 7
}
```

---

## db://schema/classes/count

Returns the total number of classes in the database schema.

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

Describes the schema of a specific class, including its superclass, declared fields, and all inherited fields. `{className}` is a **URI template parameter** — replace it with the name of the class you want to inspect (for example, `db://schema/class/Employee`).

### Parameters

| Parameter | Description |
|-----------|-------------|
| `className` | The name of the class to describe (case-sensitive). |

### Output Schema

```json
{
  "name": "string",           // class name
  "superclass": {
    "name": "string",         // parent class name
    "superclass": "string"    // grandparent class name; omitted if none
  },
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
  "superclass": {
    "name": "Worker"
  },
  "declaredFields": [
    { "name": "annualSalary", "type": "int" },
    { "name": "department", "type": "java.lang.String" },
    { "name": "performanceBonus", "type": "double" }
  ],
  "allFields": [
    { "name": "active", "type": "boolean" },
    { "name": "name", "type": "java.lang.String" },
    { "name": "annualSalary", "type": "int" },
    { "name": "department", "type": "java.lang.String" },
    { "name": "performanceBonus", "type": "double" }
  ]
}
```

---

## db://schema/complete

Returns the complete database schema with detailed field information for every class. Each entry includes the class name, superclass, declared fields, and all inherited fields. Use this when you need the full data model upfront, instead of calling `db://schema/classes` followed by multiple `db://schema/class/{className}` reads.

### Output Schema

```json
{
  "classes": [
    {
      "name": "string",           // class name
      "superclass": {
        "name": "string",         // parent class name
        "superclass": "string"    // grandparent class name; omitted if none
      },
      "declaredFields": [
        { "name": "string", "type": "string" }
      ],
      "allFields": [
        { "name": "string", "type": "string" }
      ]
    }
  ],
  "count": 0                      // total number of classes
}
```

### Example

```json
{
  "classes": [
    {
      "name": "Project",
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
      "superclass": { "name": "Worker" },
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
    "..."
  ],
  "count": 7
}
```

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](../tools/index.md)**  
  Learn about the query and schema tools exposed by the NoSQL server.

- :material-chat-processing: **[Prompts](../prompts/index.md)**  
  Discover pre-built prompt templates for common NoSQL workflows.

</div>
