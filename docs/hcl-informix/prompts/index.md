---
title: Prompts
description: Overview of the prompts available when using the Actian MCP Server with HCL Informix® Database.
---

# Prompts

The Actian MCP Server for HCL Informix® includes a built-in prompt that converts natural-language questions into expert-level database queries.

## Available Prompts

Use the following prompt to help you format the database inquiries:

| Prompt | Description |
|--------|-------------|
| [`ask_question`](#ask_question) |Converts a plain-language question into a structured prompt designed for expert database analysis. |

## ask_question

This tool takes a standard question and returns a formatted prompt string. The server applies a template that instructs the database engine to act as an expert analyst

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
  Learn more about the SQL and schema tools provided by the HCL Informix® server.

- :material-folder-open: **[Resources](../resources/index.md)**  
  Explore the various resource types available through the HCL Informix®  server.

</div>