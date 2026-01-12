# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import asyncio
import pyodbc
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastmcp.utilities.logging import get_logger
from actian_mcp_server.tools import initialize_tools
from actian_mcp_server.resources import initialize_resources
from actian_mcp_server.prompts import initialize_prompts

server_name = "Actian MCP Server"
logger = get_logger(server_name)

class ActianMCP:
    def __init__(self, conn_param: str):
        self.conn_param = conn_param
        self.connection = None

    def connect_db(self):
        logger.debug("Initializing database connection")
        try:
            logger.debug(f"Connection string: {self.conn_param}")
            self.connection = pyodbc.connect(self.conn_param)
            logger.debug("Database connection established successfully")
            # cursor = self.connection.cursor()
            return self.connection
        except Exception as e:
            logger.critical(f"Database connection error: {type(e).__name__}: {str(e)}", exc_info=True)
            raise RuntimeError("Failed to establish database connection") from e
    
    def cleanup_db(self):
        if self.connection:
            logger.debug("Closing database connection")
            try:
                self.connection.close()
            except Exception:
                logger.warning("Error closing database connection", exc_info=True)
            
def app_lifespan(conn_string):
    @asynccontextmanager
    async def create_actianmcp(server: FastMCP) -> AsyncIterator[ActianMCP]:
        actianmcp = ActianMCP(conn_string)
        try:
            # Connect using a loop.run_in_executor to avoid blocking
            loop = asyncio.get_event_loop()
            actianmcp.connection = await loop.run_in_executor(None, actianmcp.connect_db)

            logger.info(f"Initializing tools for {server_name}")
            initialize_tools(server, actianmcp)
            logger.info(f"Initializing resources for {server_name}")
            initialize_resources(server, actianmcp)
            logger.info(f"Initializing prompts for {server_name}")
            initialize_prompts(server)

            yield actianmcp
        except Exception as e:
            raise RuntimeError(f"{str(e)}")
        finally:
            await loop.run_in_executor(None, actianmcp.cleanup_db)
    return create_actianmcp

# TODO(alokaj): parse it as cli argument
conn_string = "Driver={Actian VW};database=sep_db"
server = FastMCP(server_name, lifespan=app_lifespan(conn_string))

def main():

    logger.info(f"Starting {server_name}")
    server.run(transport="stdio")

if __name__ == "__main__":
    main()
