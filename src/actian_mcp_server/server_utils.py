# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import re
import logging
import sqlglot
from sqlglot import expressions as exp

logger = logging.getLogger(__name__)

_WRITE_NODES = (
    exp.Insert, exp.Update, exp.Delete, exp.Create, exp.Drop,
    exp.Alter, exp.Grant, exp.Revoke, exp.Merge, exp.Command,
    exp.TruncateTable
)

_WRITE_PATTERN = re.compile(
    r"""
    ^\s*
    (?:
        INSERT | UPDATE | DELETE | MERGE   | TRUNCATE |
        CREATE | ALTER  | DROP   | RENAME  | MODIFY   |
        GRANT  | REVOKE |
        COPY   | CALL   | EXECUTE          |
        SET\s+SESSION
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", "", sql)
    return sql.strip()


def validate_readonly_query(query: str) -> tuple[bool, str]:
    if not query or not query.strip():
        return False, "Empty query"

    # AST-based check (walk the tree to catch CTEs/subqueries with mutations)
    try:
        statements = [s for s in sqlglot.parse(query) if s is not None]

        if not statements:
            return False, "Empty query"

        if len(statements) > 1:
            return False, "Multi-statement queries are not permitted"

        stmt = statements[0]

        # walk every node in the AST and validate against the write nodes
        for node in stmt.walk():
            if isinstance(node, _WRITE_NODES):
                return False, f"Only SELECT queries are permitted (contains {type(node).__name__})"

        return True, ""

    except Exception as e:
        logger.debug(f"sqlglot parsing failed ({type(e).__name__}: {e}), falling back to validating against a regex")

    # FALLBACK: regex check
    clean = _strip_sql_comments(query)

    if not clean:
        return False, "Empty query"

    # reject multi-statement in fallback (strip string literals first to avoid false matches)
    no_strings = re.sub(r"'[^']*'", "''", clean)
    if ";" in no_strings:
        return False, "Multi-statement queries are not permitted"

    if _WRITE_PATTERN.match(no_strings):
        return False, "Only SELECT queries are permitted"

    # actian-specific syntax that sqlglot can't parse — rely on DB readonly mode
    logger.debug("Query uses Actian-specific syntax not parsed by sqlglot; relying on DB readonly mode")
    return True, ""
