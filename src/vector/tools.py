# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import pyodbc
import asyncio
from actian_mcp_server.server_interfaces import MCPTools
from typing import List, Dict, Any

def _execute_query(query: str, connection: pyodbc.Connection) -> str:
    try:
        with connection.cursor() as cur:
            cur.execute(query)
            results: List[Dict[str, Any]] = []
            if cur.description:
                columns = [column[0] for column in cur.description]
                rows = cur.fetchall()
                results = [dict(zip(columns, map(str, row))) for row in rows]
            return str(results)
    except pyodbc.Error as e:
        return f"Error: {str(e)}"

class VectorTools(MCPTools):
    async def execute_query(self, query: str) -> str:
        """
        Execute an SQL query and fetch all the results.

        Obtains a database cursor, executes the SQL query
        and returns all results in json format.

        Parameters
            query: str
                SQL query to execute

        Returns
            str
                Query results containing columns and rows, or query error containing the pyodbc.Error message
        """
        try:
            ret = await asyncio.to_thread(_execute_query, query, self._connection)
            return ret
        except Exception as e:
            return f"Error: {str(e)}"

def initialize_vector_tools(server: FastMCP, connection: pyodbc.Connection):
    tools = VectorTools(connection)

    server.tool(name="execute_query")(tools.execute_query)
