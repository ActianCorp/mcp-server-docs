# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.
#
# Unified tool registration for Actian Zen MCP Server (9 tools).

import asyncio
import json
import re
import logging
import pyodbc
from fastmcp import FastMCP
from zen.core.connection import ZenConnection
from zen.core.orm_manager import ZenORMManager
from zen.core.ddl_manager import ZenDDLManager
from zen.core.file_operations import ZenFileManager
from zen.core.translator import translate_information_schema

_log = logging.getLogger(__name__)

try:
    from actian_mcp_server.oauth import get_current_username
except ImportError:
    def get_current_username():
        return None


def _log_authenticated_user():
    """Log the OAuth-authenticated user if present. Zen has no SET SESSION AUTHORIZATION,
    so authentication is recorded but not enforced at the database level."""
    user = get_current_username()
    if user:
        _log.info("Request from authenticated user: %s", user)


def _readonly_error(e: Exception) -> dict | None:
    """If the exception is Zen's OPENMODE=1 rejection, return a structured
    read-only notice instead of a raw error. Returns None for other exceptions."""
    msg = str(e)
    if "READ-ONLY data source" in msg or "Access denied to a READ" in msg:
        return {
            "readonly": True,
            "message": "Operation not permitted: server is running in read-only mode. "
                       "Only SELECT queries are allowed.",
        }
    return None


# ---

_IDENT_RE = re.compile(r'^[A-Za-z_][A-Za-z0-9_#]*$')

def _validate_identifier(name: str, kind: str = "identifier"):
    if not name or not _IDENT_RE.match(name):
        raise ValueError(f"Invalid {kind}: {name!r}")


# blocks string literals, comments, stacked statements, and DDL/DML keywords
# that have no place in a WHERE clause
_UNSAFE_WHERE_RE = re.compile(
    r"""['"`]|--|/\*|;"""
    r"""|\b(?:SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC(?:UTE)?|TRUNCATE)\b""",
    re.IGNORECASE
)

def _db_error(e):
    if isinstance(e, ValueError):
        return {"error": str(e)}
    if isinstance(e, pyodbc.Error):
        _log.error("pyodbc error: %s", e)
        code = e.args[0] if e.args else "unknown"
        return {"error": f"database error [{code}]"}
    _log.exception("unexpected error in tool")
    return {"error": "internal error"}


def _validate_where_clause(clause):
    # tautology (1=1) not blocked — needs a full parser; string literals and stacked statements are
    if clause and _UNSAFE_WHERE_RE.search(clause):
        raise ValueError("where_clause contains disallowed characters or keywords")


def strip_markdown_code_block(text: str) -> str:
    if not text:
        return text
    text = text.strip()
    pattern = r'^```(?:sql)?\s*\n?(.*?)\n?```$'
    match = re.match(pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text


def translate_to_zen_sql(sql: str) -> tuple:
    original_sql = sql
    was_translated = False
    message = None

    # Zen doesn't support LEN()
    if re.search(r'\bLEN\s*\(', sql, re.IGNORECASE):
        sql = re.sub(r'\bLEN\s*\(', 'CHAR_LENGTH(', sql, flags=re.IGNORECASE)
        was_translated = True
        message = "Translated LEN() to CHAR_LENGTH() for Zen compatibility"

    if 'INFORMATION_SCHEMA' in sql.upper():
        sql = translate_information_schema(sql)
        if sql != original_sql:
            was_translated = True
            message = "Translated INFORMATION_SCHEMA to Zen dbo.fSQL*() functions"

    rename_pattern = r'ALTER\s+TABLE\s+(\w+)\s+RENAME\s+TO\s+(\w+)'
    rename_match = re.search(rename_pattern, sql, re.IGNORECASE)
    if rename_match:
        old_name = rename_match.group(1)
        new_name = rename_match.group(2)
        sql = f'ALTER TABLE RENAME "{old_name}" TO "{new_name}"'
        was_translated = True
        message = f"Translated to Zen syntax: ALTER TABLE RENAME {old_name} TO {new_name}"

    if re.search(r'RENAME\s+COLUMN', sql, re.IGNORECASE):
        raise ValueError("Zen does not support RENAME COLUMN. Use DROP COLUMN followed by ADD COLUMN.")

    return sql, was_translated, message


def _truncate_constraint_names_in_sql(sql: str) -> str:
    # Zen has a 20-char limit on constraint names
    pattern = r'CONSTRAINT\s+(["\']?)(\w{21,})\1'
    def truncate_match(match):
        quote = match.group(1)
        name = match.group(2)
        return f'CONSTRAINT {quote}{name[:20]}{quote}'
    return re.sub(pattern, truncate_match, sql, flags=re.IGNORECASE)


def register_zen_tools(
    server: FastMCP,
    connection: ZenConnection,
    orm: ZenORMManager,
    ddl: ZenDDLManager,
    file_mgr: ZenFileManager,
    readonly: bool = False,
    max_rows: int = 1000
):
    """Register Zen database tools with the MCP server.

    Args:
        readonly: If True, only register read-only tools (6 of 9).
                  Skips ddl_operation, batch_operation, transaction.
                  Guards execute_query to SELECT-only, orm_operation to select-only,
                  blob_operation to download+list only.
    """

    # --- execute_query ---

    @server.tool(name="execute_query")
    async def execute_query(sql: str) -> dict:
        """
        Execute raw SQL with automatic Zen dialect translation.

        For complex queries: JOINs, subqueries, aggregations, UNION, raw DML.
        For simple single-table CRUD, prefer orm_operation instead.
        For schema changes, use ddl_operation.
        For bulk data, use batch_operation.

        Write values directly in the SQL string.
        Inline values like WHERE salary > 50000 are fine.

        Auto-translations:
        - LEN() -> CHAR_LENGTH()
        - INFORMATION_SCHEMA -> dbo.fSQL*()
        - ALTER TABLE RENAME TO -> Zen syntax
        - Constraint names truncated to 20 chars
        """
        try:
            _log_authenticated_user()
            if not sql:
                return {"error": "sql parameter is required"}

            sql = strip_markdown_code_block(sql)

            if readonly and not sql.strip().upper().startswith("SELECT"):
                return {"error": "Only SELECT queries allowed in readonly mode"}

            original_sql = sql
            sql = _truncate_constraint_names_in_sql(sql)
            sql, was_translated, message = translate_to_zen_sql(sql)

            is_select = sql.strip().upper().startswith("SELECT")

            sql_upper = sql.strip().upper()
            is_ddl = any(sql_upper.startswith(kw) for kw in
                        ["CREATE ", "DROP ", "ALTER ", "RENAME "])

            def _run():
                conn = connection.get_odbc_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute(sql)

                    if is_select:
                        rows = cursor.fetchmany(max_rows + 1)
                        truncated = len(rows) > max_rows
                        if truncated:
                            rows = rows[:max_rows]
                        cols = [col[0] for col in cursor.description] if cursor.description else []
                        return {"rows": rows, "columns": cols, "truncated": truncated}
                    else:
                        rows_affected = cursor.rowcount
                        if not connection.is_transaction_active():
                            conn.commit()
                        return {"rows_affected": rows_affected}
                finally:
                    cursor.close()

            result = await asyncio.to_thread(_run)

            if is_ddl:
                orm.clear_model_cache()

            if is_select:
                results = [dict(zip(result["columns"], row)) for row in result["rows"]]
                response = {
                    "results": results,
                    "row_count": len(results),
                    "method": "execute_query"
                }
                if result["truncated"]:
                    response["truncated"] = True
                    response["truncation_note"] = f"Results limited to {max_rows} rows. Use WHERE to narrow results."
            else:
                response = {
                    "sql": sql,
                    "rows_affected": result["rows_affected"],
                    "success": True,
                    "method": "execute_query"
                }

            if was_translated:
                response["translated"] = True
                response["translation_note"] = message
                response["original_sql"] = original_sql

            return response

        except Exception as e:
            return _readonly_error(e) or _db_error(e)

    # --- ddl_operation (skipped in readonly mode) ---

    @server.tool(name="ddl_operation")
    async def ddl_operation(
        mode: str,
        # For table operations
        table: str | None = None,
        columns: list | None = None,
        zen_options: dict | None = None,
        new_name: str | None = None,
        with_clause: str | None = None,
        # For column operations
        column_name: str | None = None,
        column_type: str | None = None,
        length: int | None = None,
        precision: int | None = None,
        scale: int | None = None,
        # For index operations
        index_name: str | None = None,
        index_columns: list | None = None,
        constraint_name: str | None = None,
        # For programmable objects
        name: str | None = None,
        parameters: list | None = None,
        body: str | None = None,
        atomic: bool = True,
        timing: str | None = None,
        event: str | None = None,
        referencing: str | None = None,
        when: str | None = None,
        returns: str | None = None,
        select_clause: str | None = None
    ) -> dict:
        """
        Schema change operations (DDL).

        Modes:
        - ddl_create_table: Create table (table + columns + optional zen_options)
        - ddl_rename_table: Rename table (table + new_name)
        - ddl_alter_table: Alter table (table + with_clause)
        - ddl_drop_table: Drop table (table)
        - ddl_add_column: Add column (table + column_name + column_type)
        - ddl_drop_column: Drop column (table + column_name)
        - ddl_create_index: Create index (table + index_name + index_columns)
        - ddl_drop_index: Drop index (table + index_name + index_columns)
        - ddl_drop_fk: Drop foreign key (table + constraint_name)
        - ddl_create_procedure: Create procedure (name + parameters + body)
        - ddl_drop_procedure: Drop procedure (name)
        - ddl_create_trigger: Create trigger (name + table + timing + event + body)
        - ddl_drop_trigger: Drop trigger (name)
        - ddl_create_function: Create function (name + parameters + returns + body)
        - ddl_drop_function: Drop function (name)
        - ddl_create_view: Create view (name + select_clause)
        - ddl_drop_view: Drop view (name)
        """
        try:
            # table ops
            if mode == "ddl_create_table":
                if not table or not columns:
                    return {"error": "table and columns required for ddl_create_table mode"}
                def _do_create():
                    result = ddl.create_table_with_zen_options(table, columns, **(zen_options or {}))
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_do_create)

            if mode == "ddl_rename_table":
                if not table or not new_name:
                    return {"error": "table and new_name required for ddl_rename_table mode"}
                def _exec():
                    result = ddl.rename_table(table, new_name)
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_exec)

            if mode == "ddl_alter_table":
                if not table or not with_clause:
                    return {"error": "table and with_clause required for ddl_alter_table mode"}
                def _exec():
                    result = ddl.alter_table_with(table, with_clause)
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_exec)

            if mode == "ddl_drop_table":
                if not table:
                    return {"error": "table required for ddl_drop_table mode"}
                def _do_drop():
                    result = ddl.drop_table(table)
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_do_drop)

            # column ops
            if mode == "ddl_add_column":
                if not table or not column_name or not column_type:
                    return {"error": "table, column_name, and column_type required for ddl_add_column mode"}
                def _exec():
                    result = ddl.add_column(table, column_name, column_type,
                                           length=length, precision=precision, scale=scale)
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_exec)

            if mode == "ddl_drop_column":
                if not table or not column_name:
                    return {"error": "table and column_name required for ddl_drop_column mode"}
                def _exec():
                    result = ddl.drop_column(table, column_name)
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_exec)

            # index ops
            if mode == "ddl_create_index":
                if not table or not index_name or not index_columns:
                    return {"error": "table, index_name, and index_columns required for ddl_create_index mode"}
                def _exec():
                    result = ddl.create_index(table, index_name, index_columns)
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_exec)

            if mode == "ddl_drop_index":
                if not table or not index_name or not index_columns:
                    return {"error": "table, index_name, and index_columns required for ddl_drop_index mode"}
                def _exec():
                    result = ddl.drop_index(table, index_name, index_columns)
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_exec)

            if mode == "ddl_drop_fk":
                if not table or not constraint_name:
                    return {"error": "table and constraint_name required for ddl_drop_fk mode"}
                def _exec():
                    result = ddl.drop_foreign_key(table, constraint_name)
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_exec)

            # programmable objects
            if mode == "ddl_create_procedure":
                if not name or parameters is None or not body:
                    return {"error": "name, parameters, and body required for ddl_create_procedure mode"}
                def _exec():
                    result = ddl.create_procedure(name, parameters, body, atomic)
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_exec)

            if mode == "ddl_drop_procedure":
                if not name:
                    return {"error": "name required for ddl_drop_procedure mode"}
                def _exec():
                    result = ddl.drop_procedure(name)
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_exec)

            if mode == "ddl_create_trigger":
                if not name or not table or not timing or not event or not body:
                    return {"error": "name, table, timing, event, and body required for ddl_create_trigger mode"}
                def _create_trig():
                    result = ddl.create_trigger(name, table, timing, event, body,
                                               referencing=referencing, when=when)
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_create_trig)

            if mode == "ddl_drop_trigger":
                if not name:
                    return {"error": "name required for ddl_drop_trigger mode"}
                def _exec():
                    result = ddl.drop_trigger(name)
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_exec)

            if mode == "ddl_create_function":
                if not name or parameters is None or not returns or not body:
                    return {"error": "name, parameters, returns, and body required for ddl_create_function mode"}
                def _exec():
                    result = ddl.create_function(name, parameters, returns, body)
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_exec)

            if mode == "ddl_drop_function":
                if not name:
                    return {"error": "name required for ddl_drop_function mode"}
                def _exec():
                    result = ddl.drop_function(name)
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_exec)

            if mode == "ddl_create_view":
                if not name or not select_clause:
                    return {"error": "name and select_clause required for ddl_create_view mode"}
                def _exec():
                    result = ddl.create_view(name, select_clause)
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_exec)

            if mode == "ddl_drop_view":
                if not name:
                    return {"error": "name required for ddl_drop_view mode"}
                def _exec():
                    result = ddl.drop_view(name)
                    orm.clear_model_cache()
                    return result
                return await asyncio.to_thread(_exec)

            return {"error": f"Unknown DDL mode: {mode}. Use: ddl_create_table, ddl_drop_table, ddl_add_column, ddl_drop_column, ddl_create_index, ddl_drop_index, ddl_create_view, ddl_drop_view, ddl_create_procedure, ddl_drop_procedure, ddl_create_function, ddl_drop_function, ddl_create_trigger, ddl_drop_trigger, ddl_rename_table, ddl_alter_table, ddl_drop_fk"}

        except Exception as e:
            return _readonly_error(e) or _db_error(e)

    # --- batch_operation ---

    @server.tool(name="batch_operation")
    async def batch_operation(
        mode: str,
        table: str,
        data: list | None = None,
        updates: dict | None = None,
        where_clause: str | None = None,
        where_params: list | None = None
    ) -> dict:
        """
        Bulk data operations and row counting.

        Modes:
        - batch_insert: Insert multiple rows (table + data)
        - batch_update: Update rows matching condition (table + updates + where_clause)
        - batch_delete: Delete rows matching condition (table + where_clause)
        - count: Get row count (table + optional where_clause)
        """
        try:
            if mode == "batch_insert":
                if not table or not data:
                    return {"error": "table and data required for batch_insert mode"}
                _validate_identifier(table, "table name")

                def _do_insert():
                    conn = connection.get_odbc_connection()
                    cursor = conn.cursor()
                    inserted = 0
                    try:
                        for row in data:
                            for col in row.keys():
                                _validate_identifier(col, "column name")
                            cols = ', '.join(row.keys())
                            placeholders = ', '.join(['?' for _ in row])
                            insert_sql = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
                            cursor.execute(insert_sql, list(row.values()))
                            inserted += 1
                        if not connection.is_transaction_active():
                            conn.commit()
                        return inserted
                    finally:
                        cursor.close()

                inserted = await asyncio.to_thread(_do_insert)
                return {"table": table, "rows_inserted": inserted, "success": True}

            if mode == "batch_update":
                if not table or not updates or not where_clause:
                    return {"error": "table, updates, and where_clause required for batch_update mode"}
                _validate_identifier(table, "table name")
                for col in updates.keys():
                    _validate_identifier(col, "column name")
                _validate_where_clause(where_clause)

                def _do_update():
                    conn = connection.get_odbc_connection()
                    cursor = conn.cursor()
                    try:
                        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
                        update_sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
                        all_params = list(updates.values()) + (where_params or [])
                        cursor.execute(update_sql, all_params)
                        rows_affected = cursor.rowcount
                        if not connection.is_transaction_active():
                            conn.commit()
                        return rows_affected
                    finally:
                        cursor.close()

                rows = await asyncio.to_thread(_do_update)
                return {"table": table, "rows_updated": rows, "success": True}

            if mode == "batch_delete":
                if not table or not where_clause:
                    return {"error": "table and where_clause required for batch_delete mode"}
                _validate_identifier(table, "table name")
                _validate_where_clause(where_clause)

                def _do_delete():
                    conn = connection.get_odbc_connection()
                    cursor = conn.cursor()
                    try:
                        delete_sql = f"DELETE FROM {table} WHERE {where_clause}"
                        cursor.execute(delete_sql, where_params or [])
                        rows_affected = cursor.rowcount
                        if not connection.is_transaction_active():
                            conn.commit()
                        return rows_affected
                    finally:
                        cursor.close()

                rows = await asyncio.to_thread(_do_delete)
                return {"table": table, "rows_deleted": rows, "success": True}

            if mode == "count":
                if not table:
                    return {"error": "table required for count mode"}
                _validate_identifier(table, "table name")
                if where_clause:
                    _validate_where_clause(where_clause)

                def _get_count():
                    conn = connection.get_odbc_connection()
                    cursor = conn.cursor()
                    try:
                        count_sql = f"SELECT COUNT(*) FROM {table}"
                        if where_clause:
                            count_sql += f" WHERE {where_clause}"
                        cursor.execute(count_sql, where_params or [])
                        return cursor.fetchone()[0]
                    finally:
                        cursor.close()

                count = await asyncio.to_thread(_get_count)
                return {"table": table, "row_count": count}

            return {"error": f"Unknown batch mode: {mode}. Use: batch_insert, batch_update, batch_delete, count"}

        except Exception as e:
            return _readonly_error(e) or _db_error(e)


    @server.tool(name="list_tables")
    async def list_tables() -> dict:
        """List all user tables in the database via Zen dbo.fSQLTables() catalog."""
        try:
            def _run():
                conn = connection.get_odbc_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "SELECT TABLE_NAME FROM dbo.fSQLTables(NULL, NULL, NULL) "
                        "WHERE TABLE_TYPE = 'TABLE' ORDER BY TABLE_NAME"
                    )
                    rows = cursor.fetchall()
                    return [row[0] for row in rows]
                finally:
                    cursor.close()

            tables = await asyncio.to_thread(_run)
            return {"tables": tables, "count": len(tables)}

        except Exception as e:
            return _db_error(e)


    @server.tool(name="describe_table")
    async def describe_table(table: str) -> dict:
        """Get schema information for a table (columns, types, keys)."""
        try:
            _validate_identifier(table, "table name")
            def _run():
                conn = connection.get_odbc_connection()
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        f"SELECT COLUMN_NAME, TYPE_NAME, PRECISION, SCALE, "
                        f"IS_NULLABLE, COLUMN_DEF, ORDINAL_POSITION "
                        f"FROM dbo.fSQLColumns(NULL, '{table}', NULL) "
                        f"ORDER BY ORDINAL_POSITION"
                    )
                    col_rows = cursor.fetchall()
                    col_names = [col[0] for col in cursor.description]

                    cursor.execute(
                        f"SELECT COLUMN_NAME FROM dbo.fSQLPrimaryKeys(NULL, '{table}')"
                    )
                    pk_rows = cursor.fetchall()
                    pk_columns = [row[0] for row in pk_rows]

                    cursor.execute(
                        f"SELECT FKTABLE_NAME, FKCOLUMN_NAME, PKTABLE_NAME, PKCOLUMN_NAME "
                        f"FROM dbo.fSQLForeignKeys(NULL, NULL, '{table}')"
                    )
                    fk_rows = cursor.fetchall()
                    foreign_keys = [
                        {
                            "column": row[1],
                            "references_table": row[2],
                            "references_column": row[3]
                        }
                        for row in fk_rows
                    ]

                    columns = []
                    for row in col_rows:
                        col_dict = dict(zip(col_names, row))
                        columns.append({
                            "name": col_dict["COLUMN_NAME"],
                            "type": col_dict["TYPE_NAME"],
                            "precision": col_dict.get("PRECISION"),
                            "scale": col_dict.get("SCALE"),
                            "nullable": col_dict["IS_NULLABLE"] == "YES",
                            "default": col_dict.get("COLUMN_DEF"),
                            "primary_key": col_dict["COLUMN_NAME"] in pk_columns
                        })

                    return {
                        "table_name": table,
                        "columns": columns,
                        "primary_keys": pk_columns,
                        "foreign_keys": foreign_keys
                    }
                finally:
                    cursor.close()

            return await asyncio.to_thread(_run)

        except Exception as e:
            return _db_error(e)

    # --- orm_operation ---

    @server.tool(name="orm_operation")
    async def orm_operation(
        operation: str,
        table: str,
        columns: list | None = None,
        where: dict | None = None,
        order_by: list | None = None,
        limit: int | None = None,
        offset: int | None = None,
        joins: list | None = None,
        group_by: list | None = None,
        having: dict | None = None,
        data: dict | None = None,
        entity_id: int | None = None
    ) -> dict:
        """
        Single-table CRUD with validation.

        Best for: simple SELECT/INSERT/UPDATE/DELETE on one table.
        For JOINs, subqueries, aggregations -> use execute_query with raw SQL.

        Operations: select, insert, update, delete
        """
        try:
            if readonly and operation in ("insert", "update", "delete"):
                return {"error": f"Operation '{operation}' not allowed in readonly mode"}

            def _execute():
                if operation == "select":
                    query_spec = {"table": table}
                    if columns:
                        query_spec["columns"] = columns
                    if where:
                        query_spec["where"] = where
                    if order_by:
                        query_spec["order_by"] = order_by
                    if offset:
                        query_spec["offset"] = offset
                    if joins:
                        query_spec["joins"] = joins
                    if group_by:
                        query_spec["group_by"] = group_by
                    if having:
                        query_spec["having"] = having
                    # apply backstop — LLM limit capped at max_rows
                    query_spec["limit"] = min(limit, max_rows) if limit else max_rows
                    result = orm.query_builder(query_spec)
                    if isinstance(result, dict) and len(result.get("results", [])) >= max_rows:
                        result["truncated"] = True
                        result["truncation_note"] = f"Results limited to {max_rows} rows. Use WHERE to narrow results."
                    return result

                elif operation == "insert":
                    if not data:
                        return {"error": "data is required for insert operation"}
                    return orm.create_entity(table, data)

                elif operation == "update":
                    if entity_id is None:
                        return {"error": "entity_id is required for update operation"}
                    if not data:
                        return {"error": "data is required for update operation"}
                    return orm.update_entity(table, entity_id, data)

                elif operation == "delete":
                    if entity_id is None:
                        return {"error": "entity_id is required for delete operation"}
                    return orm.delete_entity(table, entity_id)

                else:
                    return {"error": f"Unknown operation: {operation}. Use: select, insert, update, delete"}

            return await asyncio.to_thread(_execute)

        except Exception as e:
            return {
                **_db_error(e),
                "hint": "Check resource://database/schema for column names. Consider execute_query for complex queries.",
                "alternative": "execute_query"
            }

    # --- transaction ---

    @server.tool(name="transaction")
    async def transaction(action: str) -> dict:
        """
        Transaction control: begin, commit, rollback.
        """
        if action == "begin":
            return connection.begin_transaction()
        elif action == "commit":
            return connection.commit_transaction()
        elif action == "rollback":
            return connection.rollback_transaction()
        else:
            return {"error": f"Unknown action: {action}. Use: begin, commit, rollback"}

    # --- blob_operation ---

    @server.tool(name="blob_operation")
    async def blob_operation(
        action: str,
        table_name: str,
        file_path: str = None,
        metadata_fields: dict = None,
        file_id: int = None,
        output_path: str = None,
        id_column: str = "id",
        blob_column: str = "file_data"
    ) -> dict:
        """
        BLOB file operations: upload, download, list, delete.
        """
        try:
            if readonly and action in ("upload", "delete"):
                return {"error": f"Action '{action}' not allowed in readonly mode"}

            if action == "upload":
                if not file_path:
                    return {"error": "file_path required for upload action"}
                def _up():
                    return file_mgr.upload_file(table_name, file_path, metadata_fields)
                return await asyncio.to_thread(_up)

            elif action == "download":
                if file_id is None or not output_path:
                    return {"error": "file_id and output_path required for download action"}
                def _down():
                    return file_mgr.download_file(table_name, file_id, output_path,
                                                 id_column, blob_column)
                return await asyncio.to_thread(_down)

            elif action == "list":
                def _ls():
                    return file_mgr.list_files(table_name, id_column)
                return await asyncio.to_thread(_ls)

            elif action == "delete":
                if file_id is None:
                    return {"error": "file_id required for delete action"}
                def _del():
                    return file_mgr.delete_file(table_name, file_id, id_column)
                return await asyncio.to_thread(_del)

            else:
                return {"error": f"Unknown action: {action}. Use: upload, download, list, delete"}

        except Exception as e:
            return _db_error(e)


    @server.tool(name="database_manage")
    async def database_manage(
        action: str,
        dsn_name: str = None
    ) -> dict:
        """
        Database management: list, list_dsns, switch, capabilities, release_locks.
        """
        try:
            if action == "list":
                from zen.core.dsn_discovery import discover_zen_dsns

                def _list():
                    dsns = discover_zen_dsns()
                    return {
                        "current_dsn": connection.conn_string.split('DSN=')[1].split(';')[0] if 'DSN=' in connection.conn_string else None,
                        "available_dsns": dsns,
                        "count": len(dsns)
                    }

                return await asyncio.to_thread(_list)

            elif action == "list_dsns":
                from zen.core.dsn_discovery import discover_zen_dsns, get_dsn_registry_details

                def _list_detailed():
                    dsns = discover_zen_dsns()
                    detailed = []
                    for dsn_name, dsn_info in dsns.items():
                        details = get_dsn_registry_details(dsn_name)
                        if details:
                            detailed.append({**dsn_info, **details})
                        else:
                            detailed.append(dsn_info)
                    return {"dsns": detailed, "count": len(detailed)}

                return await asyncio.to_thread(_list_detailed)

            elif action == "switch":
                if not dsn_name:
                    return {"error": "dsn_name required for switch action"}
                _validate_identifier(dsn_name, "DSN name")

                connection.release_all_locks()
                cs = f"DSN={dsn_name}"
                if readonly:
                    cs += ";OPENMODE=1"  # preserve readonly backstop after switch
                connection.conn_string = cs

                def _test():
                    conn = connection.get_odbc_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    return True

                await asyncio.to_thread(_test)

                return {
                    "success": True,
                    "new_dsn": dsn_name,
                    "message": f"Switched to database: {dsn_name}"
                }

            elif action == "capabilities":
                return {
                    "database": "Actian Zen",
                    "version": "v16+",
                    "tools_version": "9tools",
                    "sql_features": {
                        "transactions": True,
                        "stored_procedures": True,
                        "triggers": True,
                        "user_defined_functions": True,
                        "views": True,
                        "indexes": True,
                        "foreign_keys": True,
                        "check_constraints": False,
                        "sequences": False,
                        "ctes": False,
                        "window_functions": "ORM only (auto-rewrite)",
                        "temporary_tables": "# prefix",
                        "identity_columns": True
                    },
                    "type_support": {
                        "integer_types": ["TINYINT", "SMALLINT", "INTEGER", "BIGINT"],
                        "unsigned_types": ["UTINYINT", "USMALLINT", "UINTEGER", "UBIGINT"],
                        "identity_types": ["SMALLIDENTITY", "IDENTITY", "BIGIDENTITY"],
                        "float_types": ["FLOAT", "REAL", "DOUBLE", "BFLOAT4", "BFLOAT8"],
                        "decimal_types": ["NUMERIC", "DECIMAL"],
                        "money_types": ["MONEY", "CURRENCY"],
                        "string_types": ["CHAR", "VARCHAR", "NCHAR", "NVARCHAR", "TEXT"],
                        "binary_types": ["BINARY", "VARBINARY", "LONGVARBINARY"],
                        "datetime_types": ["DATE", "TIME", "DATETIME", "TIMESTAMP", "AUTOTIMESTAMP"],
                        "boolean_types": ["BIT"]
                    },
                    "limits": {
                        "table_name_length": 20,
                        "constraint_name_length": 20,
                        "max_columns_per_table": 1024
                    }
                }

            elif action == "release_locks":
                return connection.release_all_locks()

            else:
                return {"error": f"Unknown action: {action}. Use: list, list_dsns, switch, capabilities, release_locks"}

        except Exception as e:
            return _db_error(e)

    # --- readonly mode: remove write-only tools ---
    if readonly:
        for tool_name in ("ddl_operation", "batch_operation", "transaction"):
            server.remove_tool(tool_name)
