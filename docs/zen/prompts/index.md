---
title: Prompts
description: Overview of the prompts available when using the Actian MCP Server with Actian Zen.
---

# Prompts

The Actian MCP Server for **Actian Zen** exposes a built-in prompt for general database questions.

## Available prompts

The Zen integration provides the following prompt:

| Prompt | Purpose |
|--------|---------|
| `ask_question` | Generates a Zen database expert prompt from a user question. |

## ask_question

### Description

Renders a database expert prompt from a supplied question and returns the resulting prompt text. The prompt identifies the assistant as a Zen (Actian PSQL) database expert.

### Input parameters

| Field | Type | Required | Description |
|-------|------|----------|--------------|
| `question` | `string` | Yes | User question to insert into the prompt. |

### Output schema

```text
You are a Zen (Actian PSQL) database expert. Answer the following question: <question>
```

### Example

```json
{
	"question": "What are the top 5 departments by employee count?"
}
```

```text
You are a Zen (Actian PSQL) database expert. Answer the following question: What are the top 5 departments by employee count?
```

## Next steps

- [Tools](../tools/index.md) — Learn about Zen tools
- [Resources](../resources/index.md) — Learn about Zen resources
