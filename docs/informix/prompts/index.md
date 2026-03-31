---
title: Prompts
description: Overview of the prompts available when using the Actian MCP Server with Informix Database.
---

# Prompts

The Actian MCP Server for **Informix Database** exposes a built-in prompt for general database questions.

## Available prompts

The Informix Database integration provides the following prompt:

| Prompt | Purpose |
|--------|---------|
| `ask_question` | Generates a database-oriented prompt from a user question. |

## ask_question

### Description

Renders a database expert prompt from a supplied question and returns the resulting prompt text.

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | `string` | Yes | User question to insert into the prompt. |

### Output Schema

```text
You are a database expert. Answer the following question: <question>
```

### Example

```json
{
  "question": "What are the top 5 customers by revenue this quarter?"
}
```

```text
You are a database expert. Answer the following question: What are the top 5 customers by revenue this quarter?
```

## Next steps

- [Tools](../tools/index.md) — Learn about Informix MCP server tools
- [Resources](../resources/index.md) — Learn about Informix MCP server resources