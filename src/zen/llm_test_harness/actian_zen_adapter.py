"""
Adapter for testing actian-zen server tools directly.

Provides same interface as zen_sqlalchemy_mcp_server for test compatibility.
"""

import sys
import os
import asyncio

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

from actian_zen.core.connection import ZenConnection
from actian_zen.core.orm_manager import ZenORMManager
from actian_zen.core.ddl_manager import ZenDDLManager
from actian_zen.core.type_mapper import ZenTypeMapper
from actian_zen.core.translator import translate_information_schema
from actian_zen.tools.registry import translate_to_zen_sql, strip_markdown_code_block

# Default connection string
DEFAULT_DSN = os.environ.get('ZEN_DSN', 'demodata')
DEFAULT_CONN_STRING = f"DSN={DEFAULT_DSN}"

# Global connection (lazy initialized)
_connection = None
_orm = None
_ddl = None


def get_connection():
    """Get or create ZenConnection"""
    global _connection
    if _connection is None:
        _connection = ZenConnection(DEFAULT_CONN_STRING)
    return _connection


def get_orm():
    """Get or create ORM manager"""
    global _orm
    if _orm is None:
        _orm = ZenORMManager(get_connection())
    return _orm


def get_ddl():
    """Get or create DDL manager"""
    global _ddl
    if _ddl is None:
        _ddl = ZenDDLManager(get_connection())
    return _ddl


# ════════════════════════════════════════════════════════════════════════════════
# Synchronous wrappers for test compatibility
# ════════════════════════════════════════════════════════════════════════════════

def execute_raw_sql(sql: str, parameters: list = None) -> dict:
    """Execute raw SQL query (SELECT only)"""
    try:
        sql = strip_markdown_code_block(sql)

        if not sql.strip().upper().startswith("SELECT"):
            return {"error": "Only SELECT queries allowed."}

        # Translate SQL
        translated_sql, was_translated, message = translate_to_zen_sql(sql)

        conn = get_connection().get_odbc_connection()
        cursor = conn.cursor()
        try:
            if parameters:
                cursor.execute(translated_sql, parameters)
            else:
                cursor.execute(translated_sql)
            rows = cursor.fetchall()
            columns = [col[0] for col in cursor.description] if rows else []
        finally:
            cursor.close()

        results = [dict(zip(columns, row)) for row in rows] if rows else []

        response = {
            "results": results,
            "row_count": len(results),
            "method": "raw_sql"
        }
        if was_translated:
            response["translated"] = True
            response["translation_note"] = message

        return response

    except Exception as e:
        return {"error": str(e)}


def orm_query_builder(query: dict) -> dict:
    """Execute ORM query"""
    try:
        return get_orm().execute_query(query)
    except Exception as e:
        return {"error": str(e)}


def get_zen_schema(table_name: str = None) -> dict:
    """Get schema information"""
    try:
        from sqlalchemy import inspect
        engine = get_connection().get_engine()
        inspector = inspect(engine)

        if table_name:
            columns = inspector.get_columns(table_name)
            pk = inspector.get_pk_constraint(table_name)
            return {
                "table": table_name,
                "columns": [
                    {
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col.get("nullable", True)
                    }
                    for col in columns
                ],
                "primary_key": pk.get("constrained_columns", [])
            }
        else:
            tables = inspector.get_table_names()
            return {
                "tables": tables,
                "count": len(tables)
            }
    except Exception as e:
        return {"error": str(e)}


def execute_custom_sql(sql: str, params: list = None) -> dict:
    """Execute any SQL statement"""
    try:
        sql = strip_markdown_code_block(sql)
        sql, was_translated, message = translate_to_zen_sql(sql)

        conn = get_connection().get_odbc_connection()
        cursor = conn.cursor()
        try:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            rows_affected = cursor.rowcount
            conn.commit()
        finally:
            cursor.close()

        return {
            "sql": sql,
            "rows_affected": rows_affected,
            "success": True
        }
    except Exception as e:
        return {"error": str(e)}


def insert_data(table: str, data: list) -> dict:
    """Insert rows into table"""
    try:
        conn = get_connection().get_odbc_connection()
        cursor = conn.cursor()
        inserted = 0
        try:
            for row in data:
                columns = ', '.join(row.keys())
                placeholders = ', '.join(['?' for _ in row])
                sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                cursor.execute(sql, list(row.values()))
                inserted += 1
            conn.commit()
        finally:
            cursor.close()

        return {"table": table, "rows_inserted": inserted, "success": True}
    except Exception as e:
        return {"error": str(e)}


def get_row_count(table: str, where_clause: str = None) -> dict:
    """Get row count"""
    try:
        conn = get_connection().get_odbc_connection()
        cursor = conn.cursor()
        try:
            sql = f"SELECT COUNT(*) FROM {table}"
            if where_clause:
                sql += f" WHERE {where_clause}"
            cursor.execute(sql)
            count = cursor.fetchone()[0]
        finally:
            cursor.close()

        return {"table": table, "row_count": count}
    except Exception as e:
        return {"error": str(e)}


# ════════════════════════════════════════════════════════════════════════════════
# Async versions (for MCP client tests)
# ════════════════════════════════════════════════════════════════════════════════

async def execute_raw_sql_async(sql: str, parameters: list = None) -> dict:
    """Async wrapper"""
    return await asyncio.to_thread(execute_raw_sql, sql, parameters)


async def orm_query_builder_async(query: dict) -> dict:
    """Async wrapper"""
    return await asyncio.to_thread(orm_query_builder, query)


# ════════════════════════════════════════════════════════════════════════════════
# Test helper
# ════════════════════════════════════════════════════════════════════════════════

def test_connection():
    """Test database connection"""
    try:
        result = execute_raw_sql("SELECT 1 AS test")
        if "error" in result:
            return False, result["error"]
        return True, f"Connected to {DEFAULT_DSN}"
    except Exception as e:
        return False, str(e)


if __name__ == "__main__":
    # Quick test
    ok, msg = test_connection()
    print(f"Connection test: {'OK' if ok else 'FAILED'} - {msg}")

    if ok:
        # Test schema
        schema = get_zen_schema()
        print(f"Tables: {schema.get('tables', [])[:5]}...")

        # Test query
        result = execute_raw_sql("SELECT TOP 3 * FROM employees")
        print(f"Query result: {result.get('row_count', 0)} rows")
