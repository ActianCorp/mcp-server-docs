# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import pytest
from fastmcp import Client, FastMCP
from actian_mcp_server.server import app_lifespan
from multiprocessing import Process
import os
import time
import socket

SERVER_NAME = "Vector MCP Server"
DBMS = os.getenv("DBMS")

CONF_ARGS = {
    "driver": "{Ingres}",
    "server": f"@localhost,tcp_ip,{os.getenv("II_INSTALLATION")}",
    "database": f"{os.getenv("TEST_DB_NAME")}",
    "max_connections": 10,
    "host": "localhost",
    "max_rows": 1000
}


def _skip_if_missing_env(*names: str):
    missing = [name for name in names if not os.getenv(name)]
    if missing:
        pytest.skip(f"Missing environment variables: {', '.join(missing)}")


def make_config(transport: str, port: int = 0) -> dict:
    return {
        **CONF_ARGS,
        "port": port,
        "dbms": "vector",
        "transport": transport,
        "username": os.getenv("DATABASE_USER"),
        "password": os.getenv("DATABASE_PASSWORD"),
    }


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((CONF_ARGS["host"], 0))
        return int(sock.getsockname()[1])


def _get_url(transport: str, host: str, port: int) -> str:
    path = "/sse" if transport == "sse" else "/mcp"
    return f"http://{host}:{port}{path}"


def _wait_for_port(host: str, port: int, process: Process | None = None, timeout: float = 10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process is not None and not process.is_alive():
            raise RuntimeError(f"Server process exited before opening port {port} (exit={process.exitcode})")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            if sock.connect_ex((host, port)) == 0:
                return

        time.sleep(0.1)

    raise TimeoutError(f"Timed out waiting for server on {host}:{port}")


def _run_server(transport: str, port: int):
    config = make_config(transport=transport, port=port)
    app = FastMCP(SERVER_NAME, lifespan=app_lifespan(config))
    app.run(transport=transport, host=CONF_ARGS["host"], port=port, show_banner=False)


@pytest.fixture()
def stdio_server():
    _skip_if_missing_env("DATABASE_USER", "DATABASE_PASSWORD")
    return FastMCP(
        SERVER_NAME,
        lifespan=app_lifespan(make_config("stdio")),
    )


@pytest.fixture()
def localhost_server():
    _skip_if_missing_env("DATABASE_USER", "DATABASE_PASSWORD")
    processes: list[Process] = []

    def run_server(transport: str):
        port = _get_free_port()
        proc = Process(target=_run_server, args=(transport, port), daemon=True)
        proc.start()
        try:
            _wait_for_port(CONF_ARGS["host"], port, proc)
            processes.append(proc)
            return _get_url(transport, CONF_ARGS["host"], port)
        except Exception:
            if proc.is_alive():
                proc.terminate()
                proc.join(timeout=3)
            if proc.is_alive():
                proc.kill()
                proc.join(timeout=3)
            raise

    yield run_server

    for proc in processes:
        if proc.is_alive():
            proc.terminate()
            proc.join(timeout=3)
        if proc.is_alive():
            proc.kill()
            proc.join(timeout=3)


@pytest.fixture()
def localhost_containerized_server():
    _skip_if_missing_env("DATABASE_USER", "DATABASE_PASSWORD", "MCP_SERVER_PORT_OUTSIDE_CONTAINER")
    host = "localhost"
    port_value = os.getenv("MCP_SERVER_PORT_OUTSIDE_CONTAINER")
    port = int(port_value)
    _wait_for_port(host, port)
    return _get_url("http", host, port)


@pytest.fixture()
def server(request):
    if request.param == "stdio":
        return request.getfixturevalue("stdio_server")
    if request.param == "localhost-http":
        localhost_server = request.getfixturevalue("localhost_server")
        return localhost_server("http")
    if request.param == "localhost-sse":
        localhost_server = request.getfixturevalue("localhost_server")
        return localhost_server("sse")
    if request.param == "containerized":
        return request.getfixturevalue("localhost_containerized_server")
    raise ValueError(f"Unsupported client target: {request.param}")


@pytest.fixture()
async def client(server):
    if isinstance(server, FastMCP):
        async with Client(server) as client:
            yield client
        return

    async with Client(server, timeout=5) as client:
        yield client
