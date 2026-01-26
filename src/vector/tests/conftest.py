# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import pytest
from fastmcp import Client, FastMCP
from actian_mcp_server.server import server_name, app_lifespan
from types import SimpleNamespace
from multiprocessing import Process
import time

CONF_ARGS = {
    "conn_string": "Driver={Actian VW};database=mcp_vector_db",
    "host": "127.0.0.1",
    "port": 8000
}

@pytest.fixture()
def server_url(server_localhost):
    return f'http://{CONF_ARGS["host"]}:{CONF_ARGS["port"]}/mcp'

def _server_localhost():
    transport_mode = "http"
    server = FastMCP(
        server_name,
        lifespan=app_lifespan(SimpleNamespace(dbms="vector", transport=transport_mode), conf_file_args=CONF_ARGS),
    )
    server.run(transport=transport_mode, host=CONF_ARGS["host"], port=CONF_ARGS["port"])

@pytest.fixture()
def server_localhost():
    proc = Process(target=_server_localhost, daemon=True)
    proc.start()
    time.sleep(1)
    try:
        yield
    finally:
        if proc.is_alive():
            proc.terminate()
            proc.join()

@pytest.fixture()
def server_stdio():
    transport_mode = "stdio"
    return FastMCP(
        server_name,
        lifespan=app_lifespan(SimpleNamespace(dbms="vector", transport=transport_mode), conf_file_args=CONF_ARGS),
    )

@pytest.fixture()
async def stdio_client(server_stdio):
    async with Client(server_stdio) as client:
        yield client
