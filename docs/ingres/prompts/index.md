---
title: Prompts
description: Overview of the prompts available when using the Actian MCP Server with Actian Ingres.
---

# Prompts

The Actian MCP Server for Actian Ingres includes a built-in prompt that converts natural-language questions into expert-level database queries.

## Available Prompts

| Prompt | Description |
|--------|-------------|
| [`ask_question`](#ask_question) | Formats a plain-language question into a structured prompt template designed for database experts. |

## ask_question

Renders a database expert prompt from a plain-language question and returns the formatted prompt text ready for use.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `question` | `string` | ✓ | The specific question you want to insert into the expert prompt template. |

### Output Template

```text
You are a database expert. Answer the following question: <question>
```

### Example

**Input**

```json
{
  "question": "What are the top 5 customers by revenue this quarter?"
}
```

**Output**

```text
You are a database expert. Answer the following question: What are the top 5 customers by revenue this quarter?
```

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](../tools/index.md)**  
  Learn about the SQL and schema tools provided by the Ingres server.

- :material-folder-open: **[Resources](../resources/index.md)**  
  Explore the various resource types available through the Ingres server.

</div>
