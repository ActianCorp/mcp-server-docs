# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import asyncio
import pyodbc
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastmcp.utilities.logging import get_logger

server_name = "Actian MCP Server"
logger = get_logger(server_name)

class ActianMCP:
    def __init__(self, conn_string: str):
        self.conn_string = conn_string
        self.connection = None

    def connect_db(self):
        logger.info("Initializing database connection")
        try:
            logger.debug(f"Connection string: {self.conn_string}")
            self.connection = pyodbc.connect(self.conn_string)
            logger.info("Database connection established successfully")
            return self.connection
        except Exception as e:
            logger.critical(f"Database connection error: {type(e).__name__}: {str(e)}", exc_info=True)
            raise RuntimeError("Failed to establish database connection") from e
    
    def cleanup_db(self):
        if self.connection:
            logger.info("Closing database connection")
            try:
                self.connection.close()
            except Exception:
                logger.warning("Error closing database connection", exc_info=True)

from vector.tools import initialize_vector_tools
from vector.resources import initialize_vector_resources
from vector.prompts import initialize_vector_prompts

def initialize_tools(server, actianmcp, dbms):
    if dbms == "vector":
        initialize_vector_tools(server, actianmcp)

def initialize_resources(server, actianmcp, dbms):
    if dbms == "vector":
        initialize_vector_resources(server, actianmcp)

def initialize_prompts(server, dbms):
    if dbms == "vector":
        initialize_vector_prompts(server)

def app_lifespan(args):
    @asynccontextmanager
    async def create_actianmcp(server: FastMCP) -> AsyncIterator[ActianMCP]:
        actianmcp = ActianMCP(args["conn_string"])
        try:
            actianmcp.connection = await asyncio.to_thread(actianmcp.connect_db)

            logger.info(f"Initializing tools for {server_name}")
            initialize_tools(server, actianmcp, args["dbms"])
            logger.info(f"Initializing resources for {server_name}")
            initialize_resources(server, actianmcp, args["dbms"])
            logger.info(f"Initializing prompts for {server_name}")
            initialize_prompts(server, args["dbms"])

            yield actianmcp
        except Exception as e:
            raise RuntimeError(f"{str(e)}")
        finally:
            await asyncio.to_thread(actianmcp.cleanup_db)
    return create_actianmcp

# TODO(alokaj): parse args from cmd or conf file
args = {
    "conn_string": "Driver={Actian VW};database=sep_db",
    "dbms": "vector"
}
server = FastMCP(server_name, lifespan=app_lifespan(args))

def main():

    logger.info(f"Starting {server_name}")
    server.run(transport="stdio")

if __name__ == "__main__":
    main()
