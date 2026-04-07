---
title: Resources
description: Overview of the resources available when using the Actian MCP Server with Actian NoSQL Database.
---

# Resources

The Actian MCP Server for **Actian NoSQL Database** exposes built-in resources for data discovery.

## Available resources

| Resource URI | Purpose |
|-----|-------------|
| `db://schema/classes` | Database Classes |
| `db://schema/classes/count` | Database Class Count |
| `db://schema/complete` | Complete Database Schema |

---

## db://schema/classes

### Description

List all available database classes and their inheritance hierarchy.
Returns a summary of each class including its parent class (if any).
Use this to discover the schema before describing specific classes.

### Output schema

```json
{
	"classes": [
	{
		"className": "string", // Name of the class (entity)
		"superClassName": "string|null" // Name of the superclass, or null if none 
	}
	// ...more classes
	], 
	"count": integer // Total number of classes
}
```

### Example usage

```json
{
  "jsonrpc": "2.0",
  "id": 11,
  "result": {
    "contents": [
      {
        "uri": "db://schema/classes",
        "text": "{\"classes\":[{\"name\":\"Vehicle\",\"superclass\":\"Thing\"},{\"name\":\"Car\",\"superclass\":\"Vehicle\"},{\"name\":\"Thing\"}],\"count\":3}",
        "mimeType": "application/json"
      }
    ]
  }
}
```

---

## db://schema/classes/count

### Description

Returns the total number of classes in the database schema.

### Output schema

```json
{
	"count": integer // The total number of classes in the database schema
}

```

### Example usage

```json
{
  "jsonrpc": "2.0",
  "id": 12,
  "result": {
    "contents": [
      {
        "uri": "db://schema/classes/count",
        "text": "{\"count\":3}",
        "mimeType": "application/json"
      }
    ]
  }
}
```

---

## db://schema/complete

### Description

Returns the complete database schema with detailed field information for every class.
Combines listing all classes and describing each one in a single call.
Each entry includes the class name, superclass, declared fields, and all inherited fields.
Prefer this resource when you need a complete picture of the data model upfront.

### Output schema

```json
{
	"classes": [
	{
		"className": "string", // Name of the class (entity)
		"superClassName": "string|null", // Name of the superclass, or null if none
		"declaredFields": [
		{
			"name": "string", // Field name declared in this class
			"type": "string", // Field type (e.g., "String", "Integer", "Date", "Reference", etc.)
			"reference": "boolean", // True if the field is a reference to another class
			"collection": "boolean", // True if the field is a collection (list/set)
			"nullable": "boolean", // True if the field can be null
			"description": "string|null" // Optional field description or comment
			// ...other metadata as needed
		}
		// ...more declared fields
		],
		"allFields": [
		{
			"name": "string", // Field name (declared or inherited)
			"type": "string", // Field type
			"reference": "boolean", // True if the field is a reference
			"collection": "boolean", // True if the field is a collection
			"declaredIn": "string", // Name of the class where the field is declared
			"nullable": "boolean", // True if the field can be null
			"description": "string|null" // Optional field description or comment
			// ...other metadata as needed
		}
		// ...more fields (declared + inherited) 
		]
	}
	// ...more classes
	],
	"count": integer // Total number of classes
}
```

### Example usage

```json
{
  "jsonrpc": "2.0",
  "id": 13,
  "result": {
    "contents": [
      {
        "uri": "db://schema/complete",
        "text": "{\"classes\":[{\"name\":\"Vehicle\",\"superclass\":{\"name\":\"Thing\"},\"declaredFields\":[{\"name\":\"plate\",\"type\":\"java.lang.String\"}],\"allFields\":[{\"name\":\"plate\",\"type\":\"java.lang.String\"}]},{\"name\":\"Car\",\"superclass\":{\"name\":\"Vehicle\",\"superclass\":\"Thing\"},\"declaredFields\":[{\"name\":\"somethingElse\",\"type\":\"Thing {}\"},{\"name\":\"trailer\",\"type\":\"Vehicle extends Thing {plate: java.lang.String; }\"}],\"allFields\":[{\"name\":\"plate\",\"type\":\"java.lang.String\"},{\"name\":\"somethingElse\",\"type\":\"Thing {}\"},{\"name\":\"trailer\",\"type\":\"Vehicle extends Thing {plate: java.lang.String; }\"}]},{\"name\":\"Thing\",\"declaredFields\":[],\"allFields\":[]}],\"count\":3}",
        "mimeType": "application/json"
      }
    ]
  }
}
```

