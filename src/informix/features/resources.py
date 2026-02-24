# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import pyodbc
import asyncio
from actian_mcp_server.server_interfaces import MCPResources
from typing import Dict, Any
import toons

class InformixResources(MCPResources):
    async def get_database_schema(self) -> str:
        """ 
        Retrieves the database schema with information such as the table name and for each table
        the column names and column datatypes respectively.

        Obtains a database cursor, executes the SQL query to retrieve the database schema
        and returns all results in a dictionary format.
    
        Returns
            str
                On query success: database schema in the toon (token-oriented object notation) format:

                table_1[column_count]:
                 - column_1: datatype_1
                 - column_2: datatype_2
                 - ...
                table_2[column_count]:
                 - column_1: datatype_1
                 - column_2: datatype_1
                 - ...
                ...

                On query error: error message containing the pyodbc.Error
        """

        query = """
            SELECT
                t.tabname AS table_name,
                c.colname AS collumn_name,
                CASE
                    WHEN c.coltype = 0 THEN 'CHAR'
                    WHEN c.coltype = 1 THEN 'SMALLINT'
                    WHEN c.coltype = 2 THEN 'INTEGER'
                    WHEN c.coltype = 3 THEN 'FLOAT'
                    WHEN c.coltype = 4 THEN 'SMALLFLOAT'
                    WHEN c.coltype = 5 THEN 'DECIMAL'
                    WHEN c.coltype = 6 THEN 'SERIAL'
                    WHEN c.coltype = 7 THEN 'DATE'
                    WHEN c.coltype = 8 THEN 'MONEY'
                    WHEN c.coltype = 9 THEN 'NULL'
                    WHEN c.coltype = 10 THEN 'DATETIME'
                    WHEN c.coltype = 11 THEN 'BYTE'
                    WHEN c.coltype = 12 THEN 'TEXT'
                    WHEN c.coltype = 13 THEN 'VARCHAR'
                    WHEN c.coltype = 14 THEN 'INTERVAL'
                    WHEN c.coltype = 15 THEN 'NCHAR'
                    WHEN c.coltype = 16 THEN 'NVARCHAR'
                    WHEN c.coltype = 17 THEN 'INT8'
                    WHEN c.coltype = 18 THEN 'SERIAL8'
                    WHEN c.coltype = 19 THEN 'SET'
                    WHEN c.coltype = 20 THEN 'MULTISET'
                    WHEN c.coltype = 21 THEN 'LIST'
                    WHEN c.coltype = 22 THEN 'ROW (unnamed)'
                    WHEN c.coltype = 40 THEN 'LVARCHAR'
                    WHEN c.coltype = 41 THEN 'CLOB'
                    WHEN c.coltype = 43 THEN 'BLOB'
                    WHEN c.coltype = 45 THEN 'BOOLEAN'
                    WHEN c.coltype = 52 THEN 'BIGINT'
                    WHEN c.coltype = 53 THEN 'BIGSERIAL'
                    ELSE 'OTHER (' || c.coltype || ')'
                END as column_datatype,
                c.collength AS column_length
            FROM
                systables t
            JOIN
                syscolumns c ON t.tabid = c.tabid
            WHERE
                t.tabid > 99  -- Filters out system catalog tables
                AND t.tabtype = 'T' -- Filters for actual Tables (not Views)
            ORDER BY
                t.tabname;
        """
          #  SELECT trim(T.table_name), trim(column_name), trim(column_datatype)
          #  FROM iitables T, iicolumns C
          #  WHERE T.table_name=C.table_name AND system_use='U'

        try:
            _, rows = await asyncio.to_thread(self.actiandb.execute_query, query)
            schema: Dict[str, Any] = {}
            for table, column, dtype, dlen in rows:
                schema.setdefault(table, []).append({
                    column: dtype
                })
            return str(toons.dumps(schema))
        except Exception as e:
            return f"Error: {str(e)}"

def initialize_informix_resources(server: FastMCP, actiandb):
    resources = InformixResources(actiandb)

    server.resource(uri="resource://database/schema")(resources.get_database_schema)
