# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from fastmcp import FastMCP
from fastmcp.utilities.logging import get_logger
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from .plugin import MCPPlugin
import argparse
import importlib
import json
import os
from pathlib import Path

server_name = "Actian MCP Server"
logger = get_logger(server_name)

# Plugin registry — add new databases here
PLUGINS = {
    "vector": "vector.plugin:VectorPlugin",
    "example": "example.plugin:ExamplePlugin",
}


def load_plugin(dbms: str, config: dict) -> MCPPlugin:
    """Dynamically load and instantiate the plugin for the given DBMS."""
    if dbms not in PLUGINS:
        raise ValueError(f"Unsupported DBMS: '{dbms}'. Available: {', '.join(PLUGINS)}")
    module_path, class_name = PLUGINS[dbms].rsplit(":", 1)
    module = importlib.import_module(module_path)
    plugin_class = getattr(module, class_name)
    return plugin_class(config)


def app_lifespan(config: dict):
    """Return a FastMCP lifespan that loads the plugin and delegates to it."""
    @asynccontextmanager
    async def lifespan(server: FastMCP) -> AsyncIterator[None]:
        plugin = load_plugin(config["dbms"], config)
        plugin.register_tools(server)
        plugin.register_resources(server)
        plugin.register_prompts(server)
        async with plugin.lifespan(server):
            yield
    return lifespan


def parse_args():
    parser = argparse.ArgumentParser(description="Actian MCP Server")
    parser.add_argument("--dbms", choices=list(PLUGINS.keys()), required=True,
                        help="The Actian DBMS to connect to")
    parser.add_argument("--conf-file", required=True,
                        help="Path to the JSON configuration file")
    parser.add_argument("--transport", choices=["stdio", "sse", "http", "streamable-http"],
                        default="stdio", help="MCP transport (default: stdio)")
    parser.add_argument("--username", default=os.getenv("DATABASE_USER"),
                        help="Database username (or set DATABASE_USER env var)")
    parser.add_argument("--password", default=os.getenv("DATABASE_PASSWORD"),
                        help="Database password (or set DATABASE_PASSWORD env var)")
    return parser.parse_args()


def load_config(cli_args) -> dict:
    """Merge conf.json and CLI arguments into a single config dict."""
    conf_path = Path(cli_args.conf_file).expanduser().resolve()
    if not conf_path.exists():
        logger.critical(f"Configuration file not found: {conf_path}")
        raise FileNotFoundError(f"Configuration file not found: {conf_path}")
    try:
        with open(conf_path) as f:
            file_config = json.load(f)
    except Exception:
        logger.critical(f"Failed to parse configuration file: {conf_path}", exc_info=True)
        raise

    return {
        **file_config,
        "dbms": cli_args.dbms,
        "transport": cli_args.transport,
        "username": cli_args.username,
        "password": cli_args.password,
    }


def validate_config(config: dict):
    """Validate framework-level config requirements."""
    if config.get("transport") in ("sse", "http", "streamable-http"):
        missing = [k for k in ("host", "port") if not config.get(k)]
        if missing:
            logger.critical(f"Transport '{config['transport']}' requires: {', '.join(missing)}")
            raise ValueError(f"Missing config for transport: {', '.join(missing)}")

    if not config.get("username") or not config.get("password"):
        logger.critical(
            "Database username and password are required. "
            "Pass --username/--password or set DATABASE_USER/DATABASE_PASSWORD."
        )
        raise ValueError("username and password are required")


def main():
    cli_args = parse_args()
    config = load_config(cli_args)
    validate_config(config)

    server = FastMCP(server_name, lifespan=app_lifespan(config))
    logger.info(f"Starting {server_name} (dbms={config['dbms']}, transport={config['transport']})")
    if config["transport"] in ("sse", "http", "streamable-http"):
        server.run(transport=config["transport"],
                   host=config["host"], port=config["port"])
    else:
        server.run()


if __name__ == "__main__":
    main()
