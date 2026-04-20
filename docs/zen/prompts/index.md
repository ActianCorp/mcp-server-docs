---
title: Prompts
description: Overview of the prompts available when using the Actian MCP Server with Actian Zen.
---

# Prompts

The Actian MCP Server for Actian Zen includes a built-in prompt template. This feature acts as a bridge, transforming the natural-language questions into the specific context needed for a database expert to provide accurate answers.

## Available Prompts

| Prompt | Description |
|--------|-------------|
| [`ask_question`](#ask_question) | Formats a user’s question using a specialized Zen database expert template. |

## ask_question

The `ask_question` prompt takes a plain-language question and wraps it in a template that identifies the AI assistant as a Zen (formerly Actian PSQL) database expert. This ensures the model approaches the query with the correct dialect and structural knowledge.

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
  Learn more about the SQL and schema tools exposed by the Zen server.

- :material-folder-open: **[Resources](../resources/index.md)**  
  Explore the resource types available through the Zen server.

</div>
