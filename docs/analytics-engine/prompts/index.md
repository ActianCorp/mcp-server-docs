---
title: Prompts
description: Built-in prompts available when using the Actian MCP Server with Actian Analytics Engine.
---

# Prompts

The Actian MCP Server for the Actian Analytics Engine includes a built-in prompt template. This tool bridges the gap between natural-language inquiries and the structured context an LLM needs to function as a database expert.


## Available Prompts

Use the following prompt to help you format the database inquiries:



| Prompt | Description |
|--------|-------------|
| [`ask_question`](#ask_question) | Formats a plain-language question into a structured prompt template designed for database experts. |



## ask_question

Use the ask_question prompt to transform a standard question into a formatted string ready for LLM processing. By framing the request within an expert context, you improve the accuracy and relevance of the generated SQL or data analysis.


### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `question` | `string` | ✓ | The question to insert into the prompt template. |

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
  Learn more about the SQL and schema tools provided by the Analytics Engine server.

- :material-folder-open: **[Resources](../resources/index.md)**  
  Explore the resource types available through the server.

</div>