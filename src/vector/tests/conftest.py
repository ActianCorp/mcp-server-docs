# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import pytest
from fastmcp import Client, FastMCP
from actian_mcp_server.server import server_name, app_lifespan
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


def _make_config(transport: str, port: int = 0) -> dict:
    return {
        **CONF_ARGS,
        "port": port,
        "dbms": "vector",
        "transport": transport,
        "username": os.getenv("DATABASE_USER"),
        "password": os.getenv("DATABASE_PASSWORD"),
    }


def get_free_port():
    with socket.socket() as s:
        s.bind(('', 0))
        port = s.getsockname()[1]
    return port


def _server_localhost(_transport, _port):
    config = _make_config(_transport, _port)
    server = FastMCP(server_name, lifespan=app_lifespan(config))
    server.run(transport=_transport, host=config["host"], port=config["port"])


@pytest.fixture()
def server_localhost_http():
    transport = "http"
    port = get_free_port()
    proc = Process(target=_server_localhost, args=(transport, port), daemon=True)
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
    return FastMCP(
        server_name,
        lifespan=app_lifespan(_make_config("stdio")),
    )


@pytest.fixture()
async def stdio_client(server_stdio):
    async with Client(server_stdio) as client:
        yield client
