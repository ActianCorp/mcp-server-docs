---
title: Prompts
description: Built-in prompt templates of the Actian MCP Server for VectorAI DB - find_information and store_information.
---

# Prompts

The Actian MCP Server for VectorAI DB includes two built-in prompt templates. They turn a plain request into instructions that steer the model to the right tool and to honest answers (quote what was found, say when nothing scored well).

## Available prompts

| Prompt | Mode | Description |
|--------|------|-------------|
| [`find_information`](#find_information) | read-only, read-write | Answer a question from the vector collections on this server. |
| [`store_information`](#store_information) | read-write only | Store a piece of text in a vector collection. |

---

## `find_information`

Wraps a question in instructions to search the collections with the `search` tool, use a filter only when the user named a payload field, quote the returned texts with their ids and scores, and say so when nothing scores well.

**Arguments**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `question` | string | Yes | The question to answer. |
| `collection` | string | No | A configured collection name. When empty, the prompt lists all configured collections and leaves the choice to the model. |

**Output template**

```
Find information relevant to: '<question>'

Search <the collection '<collection>' | one of: <configured names>> with the `search` tool
(natural-language query; add a `filter` only when the user named a payload field). Quote the
returned text fields and give their ids and scores. If nothing scores well, say so instead of
guessing; `list_collections` shows what exists.
```

**Usage example**

Input:

```json
{ "question": "how is a write approved", "collection": "documents" }
```

Output:

```
Find information relevant to: 'how is a write approved'

Search the collection 'documents' with the `search` tool (natural-language query; add a
`filter` only when the user named a payload field). Quote the returned text fields and give
their ids and scores. If nothing scores well, say so instead of guessing; `list_collections`
shows what exists.
```

---

## `store_information`

Registered only when `query_mode` is `read-write`. Wraps a text in instructions to store it with the `store` tool, to create the collection first if the tool reports it does not exist, to use `store_batch` for several texts, and not to retry a write the user rejected.

**Arguments**

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `text` | string | Yes | | The text to store. |
| `collection` | string | No | empty | A configured collection name. When empty, the model chooses among the configured collections. |
| `metadata` | string | No | `{}` | JSON object text passed to the `store` tool as `metadata`. |

**Output template**

```
Store this text in <collection '<collection>' | the right collection among: <configured names>> with the `store` tool:

<text>

Pass metadata <metadata> as the `metadata` argument. If the tool reports the collection does
not exist yet, call `create_collection` first. Several separate texts go into one `store_batch`
call, not repeated `store` calls. Each write asks the user for approval; do not retry a rejected
write.
```

**Usage example**

Input:

```json
{ "text": "The config file is read once at start.", "collection": "notes", "metadata": "{\"kind\": \"note\"}" }
```

Output:

```
Store this text in collection 'notes' with the `store` tool:

The config file is read once at start.

Pass metadata {"kind": "note"} as the `metadata` argument. If the tool reports the collection
does not exist yet, call `create_collection` first. Several separate texts go into one
`store_batch` call, not repeated `store` calls. Each write asks the user for approval; do not
retry a rejected write.
```

## Next steps

- [Tools](../tools/index.md): `search`, `store`, `store_batch`, `create_collection`.
- [Write support](../write-support.md): the approval each write triggers.
