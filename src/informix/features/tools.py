# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import asyncio
from actian_mcp_server.server_interfaces import MCPTools
import toons

class InformixTools(MCPTools):
    async def execute_query(self, query: str) -> str:
        """
        Execute an SQL query and fetch all the results.

        Obtains a database cursor, executes the SQL query
        and returns all results.

        Parameters
            query: str
                SQL query to execute

        Returns
            str
                On query success: results containing columns and rows in the toon (token-oriented object notation) format:

                    [row_count]{column_1,column_2,...}:
                        row_1_value_1,row_1_value_2,...
                        row_2_value_1,row_2_value_2,...
                        ...

                On query error: error message containing the pyodbc.Error
        """
        try:
            columns, rows = await asyncio.to_thread(self.actiandb.execute_query, query)
            ret = [dict(zip(columns, map(str, row))) for row in rows]
            return str(toons.dumps(ret))
        except Exception as e:
            return f"Error: {str(e)}"

    async def list_tables(self) -> str:
        """
        List all tables available in the database.

        Obtains a database cursor, executes the SQL query to retrieve the table names
        and returns the list of tables.

        Returns
            str
                On query success: results containing columns and rows in toon (token-oriented object notation):

                    [row_count]{table_name}:
                        table_name_1
                        table_name_2
                        ...

                On query error: error message containing the pyodbc.Error
        """

        query = """
            SELECT
                tabname AS table_name
            FROM
                systables
            WHERE
                tabid > 99
                AND tabtype = 'T'
            ORDER BY
                tabname;
        """
        #    SELECT trim(table_name) AS table_name
        #    FROM iitables
        #    WHERE system_use='U'
        try:
            columns, rows = await asyncio.to_thread(self.actiandb.execute_query, query)
            ret = [dict(zip(columns, map(str, row))) for row in rows]
            return str(toons.dumps(ret))
        except Exception as e:
            return f"Error: {str(e)}"

    async def describe_table(self, table_name: str) -> str:
        """
        Retrieves the table schema from the database with information such as the column name, column datatype,
        column length and column scale.

        Obtains a database cursor, executes the SQL query to retrieve the table schema
        and returns all results.

        Parameters
            table_name: str
                Name of the table to describe

        Returns
            str
                On query success: results containing columns and rows in toon (token-oriented object notation):

                    [row_count]{column_name, column_datatype, column_length, column_scale}:
                        column_name_1,column_datatype_1,column_length_1,column_scale_1
                        column_name_2,column_datatype_2,column_length_2,column_scale_2
                        ...

                On query error: error message containing the pyodbc.Error
        """

        query = """
            SELECT
                c.colname AS column_name,
                CASE
                    WHEN MOD(c.coltype, 256) = 0 THEN 'CHAR'
                    WHEN MOD(c.coltype, 256) = 1 THEN 'SMALLINT'
                    WHEN MOD(c.coltype, 256) = 2 THEN 'INTEGER'
                    WHEN MOD(c.coltype, 256) = 3 THEN 'FLOAT'
                    WHEN MOD(c.coltype, 256) = 5 THEN 'DECIMAL'
                    WHEN MOD(c.coltype, 256) = 6 THEN 'SERIAL'
                    WHEN MOD(c.coltype, 256) = 7 THEN 'DATE'
                    WHEN MOD(c.coltype, 256) = 8 THEN 'MONEY'
                    WHEN MOD(c.coltype, 256) = 10 THEN 'DATETIME'
                    WHEN MOD(c.coltype, 256) = 13 THEN 'VARCHAR'
                    WHEN MOD(c.coltype, 256) = 15 THEN 'NCHAR'
                    WHEN MOD(c.coltype, 256) = 16 THEN 'NVARCHAR'
                    WHEN MOD(c.coltype, 256) = 40 THEN 'LVARCHAR'
                    WHEN MOD(c.coltype, 256) = 45 THEN 'BOOLEAN'
                    WHEN MOD(c.coltype, 256) = 52 THEN 'BIGINT'
                    WHEN MOD(c.coltype, 256) = 53 THEN 'BIGSERIAL'
                    ELSE 'OTHER (' || c.coltype || ')'
                END as column_datatype,
                c.collength AS column_length,
                CASE
                    WHEN c.coltype < 256 THEN 'YES'
                    ELSE 'NO'
                END as allows_nulls
            FROM
                syscolumns c
            JOIN
                systables t ON c.tabid = t.tabid
            WHERE
                t.tabname=?
        """


        #    SELECT trim(column_name) AS column_name,
        #           trim(column_datatype) AS column_datatype,
        #           trim(column_length) AS column_length,
        #           trim(column_scale) AS column_scale
        #    FROM iitables T, iicolumns C
        #    WHERE T.table_name=C.table_name AND T.table_name=? AND system_use='U'
        try:
            columns, rows = await asyncio.to_thread(self.actiandb.execute_query, query, params=(table_name,))
            ret = [dict(zip(columns, map(str, row))) for row in rows]
            return str(toons.dumps(ret))
        except Exception as e:
            return f"Error: {str(e)}"

def initialize_informix_tools(server: FastMCP, actiandb):
    tools = InformixTools(actiandb)

    server.tool(name="execute_query")(tools.execute_query)
    server.tool(name="list_tables")(tools.list_tables)
    server.tool(name="describe_table")(tools.describe_table)
