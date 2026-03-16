# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

query_instructions = """
A read-only SQL query to be executed against Actian Analytics Engine (formerly Actian Vector) database.

You must generate correct SQL for Actian Analytics Engine dialect.
Follow these specific rules for read-only queries (SELECT) to ensure compatibility and correctness:

**Row Limiting & Pagination**:
- Use the `LIMIT <count>` clause to restrict the number of rows (e.g., `LIMIT 10`).
- Use `OFFSET <skip>` for pagination (e.g., `LIMIT 10 OFFSET 5`).

**Date & Time Functions**:
- Use `CURRENT_DATE` for the current date and `CURRENT_TIMESTAMP` for the current timestamp.
- Use the `DATE_PART('part', date_expr)` function for extracting components (e.g., `DATE_PART('year', my_date)`).
- For date arithmetic, you can use interval literals (e.g., `my_date + INTERVAL '1' DAY`, `my_date + INTERVAL '2' MONTH`).

**Data Types & Literals**:
- Use standard ANSI literals for dates: `DATE 'YYYY-MM-DD'` and `TIMESTAMP 'YYYY-MM-DD HH:MM:SS'`.
- Boolean literals `TRUE` and `FALSE` are supported.
- String literals must use single quotes `'value'`.

**Identifiers**:
- If an identifier (table or column name) contains spaces, special characters, or is a reserved keyword, enclose it in double quotes `""` (e.g., `"Order Details"`).
- Otherwise, unquoted identifiers are case-insensitive.

**Pattern Matching**:
- Use the standard `LIKE` operator with `%` and `_` wildcards.
- For more complex patterns, use the standard `LIKE_REGEX` operator with XQuery regular expression syntax (e.g., `col1 LIKE_REGEX 'H.*o W.*d'`).

**Null Handling**:
- Use `COALESCE(expr1, expr2)` to handle NULL values (standard compliant).

Do not generate DDL (CREATE, DROP) or DML statements (INSERT, UPDATE, DELETE).
The query should be a valid `SELECT` statement that answers the user's question.
"""