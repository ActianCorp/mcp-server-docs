# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import pytest
from fastmcp import Client, FastMCP
from actian_mcp_server.server import server_name, app_lifespan
from types import SimpleNamespace
from multiprocessing import Process
import socket
import os

CONF_ARGS = {
    "driver": "{Ingres VW}",
    "server": "@localhost,tcp_ip,VW",
    "database": "mcp_vector_db",
    "max_connections": 10,
    "host": "127.0.0.1",
    "port": 0,
}

def get_free_port():
    with socket.socket() as s:
        s.bind(('', 0))
        port = s.getsockname()[1]
    return port

def _server_localhost(_transport, _port):
    conf_args = dict(CONF_ARGS)
    conf_args["port"] = _port
    server = FastMCP(
        server_name,
        lifespan=app_lifespan(
            SimpleNamespace(dbms="vector", transport=_transport, username=os.getenv("DATABASE_USER"), password=os.getenv("DATABASE_PASSWORD")),
            conf_file_args=conf_args,
        ),
    )
    server.run(transport=_transport, host=conf_args["host"], port=conf_args["port"])

@pytest.fixture()
def server_localhost_http():
    transport = "http"
    port = get_free_port()
    proc = Process(target=_server_localhost, args=(transport, port,), daemon=True)
    proc.start()
    try:
        yield "http://%s:%s/mcp" % (CONF_ARGS["host"], port)
    finally:
        if proc.is_alive():
            proc.terminate()
            proc.join()

@pytest.fixture()
def server_localhost_sse():
    transport = "sse"
    port = get_free_port()
    proc = Process(target=_server_localhost, args=(transport, port), daemon=True)
    proc.start()
    try:
        yield "http://%s:%s/sse" % (CONF_ARGS["host"], port)
    finally:
        if proc.is_alive():
            proc.terminate()
            proc.join()

@pytest.fixture()
def server_stdio():
    transport = "stdio"
    return FastMCP(
        server_name,
        lifespan=app_lifespan(
            SimpleNamespace(dbms="vector", transport=transport, username=os.getenv("DATABASE_USER"), password=os.getenv("DATABASE_PASSWORD")),
            conf_file_args=CONF_ARGS
        ),
    )

@pytest.fixture()
async def stdio_client(server_stdio):
    async with Client(server_stdio) as client:
        yield client
