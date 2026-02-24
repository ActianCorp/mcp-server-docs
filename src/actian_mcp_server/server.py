# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import sys
import struct

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
import os

server_name = "Actian MCP Server"
logger = get_logger(server_name)


class ActianDB:
    def __init__(self, cli_args, conf_file_args):
        self.driver = conf_file_args["driver"]
        self.server = conf_file_args["server"]
        self.database = conf_file_args["database"]
        self.host = conf_file_args["host"]
        self.port = conf_file_args["port"]
        self.uid = cli_args.username
        self.pwd = cli_args.password
        self.dsn = conf_file_args["dsn"]
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
                                 dsn=self.dsn,
                                 uid=self.uid,
                                 pwd=self.pwd,
                                 database=self.database
            )
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
        from vector.features.tools import initialize_vector_tools
        initialize_vector_tools(server, actiandb)
    elif actiandb.dbms == "informix":
        from informix.features.tools import initialize_informix_tools
        initialize_informix_tools(server, actiandb)
    else:
        logger.error(f"There is no support for {actiandb.dbms}")
        raise

def initialize_resources(server: FastMCP, actiandb: ActianDB):
    logger.info(f"Initializing resources for {actiandb.dbms}")
    if actiandb.dbms == "vector":
        from vector.features.resources import initialize_vector_resources
        initialize_vector_resources(server, actiandb)
    elif actiandb.dbms == "informix":
        from informix.features.resources import initialize_informix_resources
        initialize_informix_resources(server, actiandb)
    else:
        logger.error(f"There is no support for {actiandb.dbms}")
        raise

def initialize_prompts(server: FastMCP, actiandb: ActianDB):
    logger.info(f"Initializing prompts for {actiandb.dbms}")
    if actiandb.dbms == "vector":
        from vector.features.prompts import initialize_vector_prompts
        initialize_vector_prompts(server)
    elif actiandb.dbms == "informix":
        from informix.features.prompts import initialize_informix_prompts
        initialize_informix_prompts(server)
    else:
        logger.error(f"There is no support for {actiandb.dbms}")
        raise

def validate_args(conf_file_args, cli_args):
    required_args = ["driver", "database", "max_connections"]
    if cli_args.transport in ["sse", "http"]:
        required_args.append("host")
        required_args.append("port")
    missing_or_empty = []
    for arg in required_args:
        if arg not in conf_file_args.keys() or conf_file_args[arg] in (None, ""):
            missing_or_empty.append(arg)

    if missing_or_empty:
        logger.critical(f"Required arguments in the configuration file are missing: {', '.join(missing_or_empty)}")
        raise

    if cli_args.username in (None, "") or cli_args.password in (None, ""):
        logger.critical("The database username or password cannot be None or empty. " \
                        "Please provide them as CLI arguments (--username, --password) " \
                        "and/or environment variables (DATABASE_USERNAME, DATABASE_PASSWORD).")
        raise

def load_conf_json(conf_file: str):
    if conf_file in (None, ""):
        logger.error("The CLI argument conf-file cannot be None or empty. Please provide a path to the configuration file.")
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
        choices=["vector","informix"],
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
        choices=["stdio", "sse", "http", "streamable-http"],
        required=False,
        help="Transport for the communication",
        default="stdio"
    )

    # Username and password parameters can be passed as CLI arguments and/or environment variables
    parser.add_argument(
        "--username",
        required=False,
        help="Database username",
        default=os.getenv("DATABASE_USER")
    )

    parser.add_argument(
        "--password",
        required=False,
        help="Database username",
        default=os.getenv("DATABASE_PASSWORD")
    )

    return parser.parse_args()

def main():
    cli_args = parse_args()
    conf_file_args = load_conf_json(cli_args.conf_file)
    validate_args(conf_file_args, cli_args)

    server = FastMCP(server_name, lifespan=app_lifespan(cli_args, conf_file_args))
    logger.info(f"Starting {server_name}")
    if cli_args.transport in ["sse", "http", "streamable-http"]:
        server.run(transport=cli_args.transport, host=conf_file_args["host"], port=conf_file_args["port"])
    else:
        server.run()

if __name__ == "__main__":
    main()
