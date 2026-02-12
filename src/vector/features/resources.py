# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import pyodbc
import asyncio
from actian_mcp_server.server_interfaces import MCPResources
from typing import Dict, Any
import toons

def _get_database_schema(actiandb: Any) -> str:
    try:
        with actiandb.get_cursor() as cur:
            query = """
                SELECT trim(T.table_name), trim(column_name), trim(column_datatype)
                FROM iitables T, iicolumns C
                WHERE T.table_name=C.table_name AND system_use='U'
            """
            schema: Dict[str, Any] = {}
            cur.execute(query)
            rows = cur.fetchall()
            for table, column, dtype in rows:
                schema.setdefault(table, []).append({
                    column: dtype
                })
            return str(toons.dumps(schema))
    except pyodbc.Error as e:
        return f"Error: {str(e)}"

class VectorResources(MCPResources):
    async def get_database_schema(self) -> str:
        """
        Get the database schema.

        Obtains a database cursor, extracts the database schema for 
        and returns all results in a dictionary format.

        Returns
            str
                Database schema in the format:

                {'table_1': [{'col_1': 'dtype_col_1'}, {'col_2': 'dtype_col_2'}, ...],
                 'table_2': [{'col_1': 'dtype_col_1'}, {'col_2': 'dtype_col_2'}, ...],
                 ...}

                or query error containing the pyodbc.Error message
        """
        try:
            ret = await asyncio.to_thread(_get_database_schema, self.actiandb)
            return ret
        except Exception as e:
            return f"Error: {str(e)}"
    
def initialize_vector_resources(server: FastMCP, actiandb):
    resources = VectorResources(actiandb)

    server.resource(uri="resource://database/schema")(resources.get_database_schema)
