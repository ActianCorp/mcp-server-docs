---
title: Prompts
description: Define reusable prompt templates that guide AI agents through common workflows.
---

# Prompts

MCP **prompts** are reusable message templates that guide an AI agent through a specific workflow. They pre-populate context, instructions, and data — reducing the need for the user to craft detailed prompts manually.

---

## Anatomy of a Prompt

A prompt has:

- **Name** — unique identifier (e.g., `analyze_table`)
- **Description** — what workflow it assists with
- **Arguments** — optional parameters that are interpolated into the template
- **Messages** — the rendered conversation history to inject

---

## Defining a Prompt

```python
# features/prompts.py
from mcp.server import Server
from mcp.types import Prompt, PromptArgument, PromptMessage, TextContent
from mcp.types import Role

def register_prompts(server: Server):

    @server.list_prompts()
    async def list_prompts():
        return [
            Prompt(
                name="analyze_table",
                description=(
                    "Analyze a database table: summarize its structure, "
                    "suggest useful queries, and flag data quality issues."
                ),
                arguments=[
                    PromptArgument(
                        name="table_name",
                        description="Name of the table to analyze.",
                        required=True
                    )
                ]
            ),
            Prompt(
                name="generate_report",
                description="Generate a natural language report from a SQL query result.",
                arguments=[
                    PromptArgument(
                        name="query",
                        description="The SQL query whose results should be narrated.",
                        required=True
                    )
                ]
            )
        ]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict):
        if name == "analyze_table":
            table = arguments.get("table_name", "unknown")
            return {
                "messages": [
                    PromptMessage(
                        role=Role.user,
                        content=TextContent(
                            type="text",
                            text=(
                                f"Please analyze the database table `{table}`.\n\n"
                                "1. Describe its structure and purpose\n"
                                "2. List the most useful SELECT queries for it\n"
                                "3. Identify any potential data quality concerns\n"
                                "Use the available tools to inspect the schema first."
                            )
                        )
                    )
                ]
            }
```

---

## Built-in Prompts

| Prompt | Description |
|--------|-------------|
| `analyze_table` | Summarise a table's structure and suggest queries |
| `generate_report` | Narrate query results in plain language |
| `optimize_query` | Review a SQL query and suggest performance improvements |
| `data_quality_check` | Check a table for nulls, duplicates, and anomalies |

---

## Best Practices

- Make prompts **task-focused** — one prompt per workflow
- Include instructions to use available tools (schema introspection, query execution)
- Use `arguments` so prompts are reusable across different tables/queries
- Write descriptions that help AI clients surface the right prompt to users
