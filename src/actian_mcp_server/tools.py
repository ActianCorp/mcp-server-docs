# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import asyncio

def run_query(conn: str, query: str):
    cursor = conn.cursor()
    results = []
    try:
        cursor.execute(query)
        if cursor.description:  # Check if the query returns results
            columns = [column[0] for column in cursor.description]
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
        return {"success": True, "results": results, "rowCount": len(results)}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        cursor.close()

def initialize_tools(server: FastMCP, actianmcp):
    @server.tool
    def print_text(text: str) -> str:
        return f"{text}"

    @server.tool()
    async def query_sql(query: str) -> str:
        """
        Tool to query the SQL database with a custom query.

        Args:
            query: The SQL query to execute.

        Returns:
            The query results as a string.
        """
        try:
            # Execute query in a non-blocking way
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, run_query, actianmcp.connection, query)

            if result["success"]:
                return f"Query results: {result['results']}"
            else:
                return f"Query error: {result['error']}"
        except Exception as e:
            return f"Error: {str(e)}"
