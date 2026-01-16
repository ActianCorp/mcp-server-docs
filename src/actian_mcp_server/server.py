# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import asyncio
import pyodbc
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from fastmcp.utilities.logging import get_logger
import argparse
import json
import os
from pathlib import Path

server_name = "Actian MCP Server"
logger = get_logger(server_name)

class ActianDB:
    def __init__(self, conn_string: str, transport: str):
        self.conn_string = conn_string
        self.transport = transport
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

def initialize_tools(server: FastMCP, connection: pyodbc.Connection, dbms: str):
    logger.info(f"Initializing tools for {server_name}")
    if dbms == "vector":
        initialize_vector_tools(server, connection)

def initialize_resources(server: FastMCP, connection: pyodbc.Connection, dbms: str):
    logger.info(f"Initializing resources for {server_name}")
    if dbms == "vector":
        initialize_vector_resources(server, connection)

def initialize_prompts(server: FastMCP, dbms: str):
    logger.info(f"Initializing prompts for {server_name}")
    if dbms == "vector":
        initialize_vector_prompts(server)

def load_conf_json(dbms: str):
    src_dir = Path(__file__).resolve().parents[1]
    conf_file = os.path.join(src_dir, dbms, "conf.json")
    with open(conf_file, 'r') as f:
        return json.load(f)

def app_lifespan(args):
    @asynccontextmanager
    async def create_actiandb(server: FastMCP) -> AsyncIterator[ActianDB]:
        try:
            conf_args = load_conf_json(args.dbms)
            actiandb = ActianDB(conf_args["conn_string"], args.transport)
            actiandb.connection = await asyncio.to_thread(actiandb.connect_db)

            initialize_tools(server, actiandb.connection, args.dbms)
            initialize_resources(server, actiandb.connection, args.dbms)
            initialize_prompts(server, args.dbms)

            yield actiandb
        except Exception as e:
            raise RuntimeError(f"{str(e)}")
        finally:
            await asyncio.to_thread(actiandb.cleanup_db)
    return create_actiandb

def parse_args():
    parser = argparse.ArgumentParser(description="Actian MCP Server Arguments")
    parser.add_argument("--dbms", type=str, required=True, help="The Actian DBMS Name")
    parser.add_argument("--transport", type=str, required=False, help="Transport for the communication", default="stdio")
    return parser.parse_args()

def main():
    args = parse_args()
    server = FastMCP(server_name, lifespan=app_lifespan(args))
    logger.info(f"Starting {server_name}")
    server.run(args.transport)

if __name__ == "__main__":
    main()
