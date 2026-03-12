# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import asyncio
import json
from fastmcp import FastMCP
from sqlalchemy import inspect, text
from zen.core.connection import ZenConnection

_zen_connection = None
_readonly_mode = False


def _get_engine():
    if _zen_connection is None:
        raise RuntimeError("Resources not initialized. Call initialize_zen_resources() first.")
    return _zen_connection.get_engine()


def _get_type_mapper():
    from zen.core.type_mapper import ZenTypeMapper
    return ZenTypeMapper()


async def get_full_schema_resource() -> str:
    """MCP Resource: complete database schema (resource://database/schema)."""
    try:
        def _build_schema():
            engine = _get_engine()
            inspector = inspect(engine)
            type_mapper = _get_type_mapper()

            schema = {
                "database": "demodata",
                "tables": {},
                "summary": {
                    "total_tables": 0,
                    "total_columns": 0,
                    "timestamp": None
                }
            }

            tables = inspector.get_table_names()
            schema["summary"]["total_tables"] = len(tables)

            for table_name in tables:
                try:
                    columns = inspector.get_columns(table_name)
                    pk = inspector.get_pk_constraint(table_name)
                    fks = inspector.get_foreign_keys(table_name)
                    indexes = inspector.get_indexes(table_name)

                    try:
                        with engine.connect() as conn:
                            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                            row_count = result.scalar()
                    except:
                        row_count = "unknown"

                    enriched_columns = []
                    for col in columns:
                        type_info = type_mapper.get_type_info(col['type'])
                        col_info = {
                            "name": col['name'],
                            "type": str(col['type']),
                            "zen_type": type_info.get('zen_type', str(col['type'])),
                            "nullable": col.get('nullable', True),
                            "autoincrement": col.get('autoincrement', False)
                        }
                        if hasattr(col['type'], 'length') and col['type'].length:
                            col_info["length"] = col['type'].length
                        if hasattr(col['type'], 'precision') and col['type'].precision:
                            col_info["precision"] = col['type'].precision
                            col_info["scale"] = getattr(col['type'], 'scale', None)
                        enriched_columns.append(col_info)

                    schema["summary"]["total_columns"] += len(enriched_columns)

                    fk_list = [
                        {
                            "columns": fk.get('constrained_columns', []),
                            "references_table": fk.get('referred_table'),
                            "references_columns": fk.get('referred_columns', [])
                        }
                        for fk in fks
                    ]
                    index_list = [
                        {
                            "name": idx.get('name'),
                            "columns": idx.get('column_names', []),
                            "unique": idx.get('unique', False)
                        }
                        for idx in indexes
                    ]

                    schema["tables"][table_name] = {
                        "columns": enriched_columns,
                        "primary_key": pk.get('constrained_columns', []) if pk else [],
                        "foreign_keys": fk_list,
                        "indexes": index_list,
                        "row_count": row_count
                    }

                except Exception as e:
                    print(f"Warning: Could not get schema for table {table_name}: {e}")
                    continue

            from datetime import datetime
            schema["summary"]["timestamp"] = datetime.now().isoformat()
            return schema

        schema = await asyncio.to_thread(_build_schema)
        return json.dumps(schema, indent=2, default=str)

    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


def initialize_zen_resources(server: FastMCP, connection: ZenConnection, readonly: bool = False):
    global _zen_connection, _readonly_mode
    _zen_connection = connection
    _readonly_mode = readonly

    @server.resource(uri="resource://database/schema")
    async def database_schema_resource() -> str:
        """Complete schema with all table/column names and types."""
        return await get_full_schema_resource()
