# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
import asyncio
import pyodbc
from contextlib import asynccontextmanager, contextmanager
from collections.abc import AsyncIterator
from fastmcp.utilities.logging import get_logger
import argparse
import json
from pathlib import Path
from dbutils.pooled_db import PooledDB

server_name = "Actian MCP Server"
logger = get_logger(server_name)

class ActianDB:
    def __init__(self, cli_args, conf_file_args):
        self.driver = conf_file_args["driver"]
        self.database = conf_file_args["database"]
        self.host = conf_file_args["host"]
        self.port = conf_file_args["port"]
        self.dbms = cli_args.dbms
        self.transport = cli_args.transport
        self.pool = None

    def create_pool(self, max_connections):
        logger.info("Initializing database connection pool")
        try:
            self.pool = PooledDB(creator=pyodbc,
                                 mincached=2,                    # idle connections opened at startup
                                 maxcached=5,                    # max idle connections
                                 maxconnections=max_connections, # max connections to the db at once
                                 blocking=True,                  # wait for a free connection
                                 driver=self.driver,
                                 database=self.database)
            logger.info("Database connection established successfully")
            return self.pool
        except Exception as e:
            logger.critical(f"Database connection error: {type(e).__name__}: {str(e)}", exc_info=True)
            raise RuntimeError("Failed to establish database connection pool") from e

    @contextmanager
    def get_cursor(self):
        logger.info("Getting a database cursor")
        try:
            connection = self.pool.connection()
            cursor = connection.cursor()
            yield cursor
        except Exception as e:
            logger.critical(f"Database connection error: {type(e).__name__}: {str(e)}", exc_info=True)
            raise RuntimeError("Failed to get the database connection or cursor") from e
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()
    
    def execute_query(self, query: str, params=None) -> str:
        columns = None
        rows = None
        try:
            with self.get_cursor() as cur:
                if params:
                    cur.execute(query, params)
                else:
                    cur.execute(query)
                if cur.description:
                    columns = [column[0] for column in cur.description]
                    rows = cur.fetchall()
                return columns, rows
        except pyodbc.Error as e:
            return f"Error: {str(e)}"

    def cleanup_pool(self):
        if self.pool:
            logger.info("Closing the database connection pool")
            try:
                self.pool.close()
            except Exception:
                logger.warning("Error closing the database connection pool", exc_info=True)

def initialize_tools(server: FastMCP, actiandb: ActianDB):
    logger.info(f"Initializing tools for {actiandb.dbms}")
    if actiandb.dbms == "vector":
        from vector.tools import initialize_vector_tools
        initialize_vector_tools(server, actiandb)
    else:
        logger.error(f"There is no support for {actiandb.dbms}")
        raise

def initialize_resources(server: FastMCP, actiandb: ActianDB):
    logger.info(f"Initializing resources for {actiandb.dbms}")
    if actiandb.dbms == "vector":
        from vector.resources import initialize_vector_resources
        initialize_vector_resources(server, actiandb)
    else:
        logger.error(f"There is no support for {actiandb.dbms}")
        raise

def initialize_prompts(server: FastMCP, actiandb: ActianDB):
    logger.info(f"Initializing prompts for {actiandb.dbms}")
    if actiandb.dbms == "vector":
        from vector.prompts import initialize_vector_prompts
        initialize_vector_prompts(server)
    else:
        logger.error(f"There is no support for {actiandb.dbms}")
        raise

def validate_conf_file_args(conf_file_args: dict, transport: str):
    required_args = ["driver", "database", "max_connections"]
    if transport in ["sse", "http"]:
        required_args.append("host")
        required_args.append("port")
    missing_or_empty = []
    for arg in required_args:
        if arg not in conf_file_args.keys() or conf_file_args[arg] in (None, ""):
            missing_or_empty.append(arg)

    if missing_or_empty:
        logger.critical(f"Required arguments in the configuration file are missing: {', '.join(missing_or_empty)}")
        raise

def load_conf_json(conf_file: str):
    if conf_file is None:
        logger.error(f"conf_file cannot be None. Please provide a path to the configuration file.")
        raise
    full_conf_file = str(Path(conf_file).expanduser().resolve())
    try:
        with open(full_conf_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {full_conf_file}")
        raise
    except Exception:
        logger.error(f"Unexpected error loading the configuration file: {full_conf_file}")
        raise

def app_lifespan(cli_args, conf_file_args):
    @asynccontextmanager
    async def create_actiandb(server: FastMCP) -> AsyncIterator[ActianDB]:
        try:
            actiandb = ActianDB(cli_args, conf_file_args)
            actiandb.pool = await asyncio.to_thread(actiandb.create_pool, conf_file_args["max_connections"])

            initialize_tools(server, actiandb)
            initialize_resources(server, actiandb)
            initialize_prompts(server, actiandb)

            yield actiandb
        except Exception as e:
            raise RuntimeError(f"{str(e)}")
        finally:
            await asyncio.to_thread(actiandb.cleanup_pool)
    return create_actiandb

def parse_args():
    parser = argparse.ArgumentParser(description="Actian MCP Server Arguments")
    parser.add_argument(
        "--dbms",
        choices=["vector"],
        required=True,
        help="The Actian DBMS name"
    )
    parser.add_argument(
        "--conf-file",
        required=True,
        help="The Actian DBMS configuration file"
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "http"],
        required=False,
        help="Transport for the communication",
        default="stdio"
    )
    return parser.parse_args()

def main():
    cli_args = parse_args()
    conf_file_args = load_conf_json(cli_args.conf_file)
    validate_conf_file_args(conf_file_args, cli_args.transport)

    server = FastMCP(server_name, lifespan=app_lifespan(cli_args, conf_file_args))
    logger.info(f"Starting {server_name}")
    if cli_args.transport in ["sse", "http"]:
        server.run(transport=cli_args.transport, host=conf_file_args["host"], port=conf_file_args["port"])
    else:
        server.run()

if __name__ == "__main__":
    main()
