---
title: Prompts
description: Overview of the prompts available when using the Actian MCP Server with Actian Zen.
---

# Prompts

The Actian MCP Server for **Actian Zen** provides a built-in prompt that transforms natural-language questions into structured, database-expert queries.

## Available Prompts

| Prompt | Description |
|--------|-------------|
| [`ask_question`](#ask_question) | Wraps a user question in a Zen database expert prompt template. |

## ask_question

Renders a database expert prompt from a plain-language question and returns the formatted prompt text ready for use. The prompt identifies the assistant as a Zen (Actian PSQL) database expert.

### Parameters

| Field | Type | Required | Description |
|-------|------|:--------:|-------------|
| `question` | `string` | ✓ | The question to insert into the prompt template. |

### Output Template

```text
You are a Zen (Actian PSQL) database expert. Answer the following question: <question>
```

### Example

**Input**

```json
{
  "question": "What are the top 5 departments by employee count?"
}
```

**Output**

```text
You are a Zen (Actian PSQL) database expert. Answer the following question: What are the top 5 departments by employee count?
```

## Next Steps

<div class="grid cards" markdown>

- :material-tools: **[Tools](../tools/index.md)**  
  Learn about the SQL and schema tools exposed by the Zen server.

- :material-folder-open: **[Resources](../resources/index.md)**  
  Explore the resource types available through the Zen server.

</div>
