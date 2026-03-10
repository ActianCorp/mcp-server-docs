# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from multiprocessing import Process

import pytest
from fastmcp import Client, FastMCP
import socket
import time
import json

from actian_mcp_server import server

MOCK_SERVER_NAME = "Mock MCP Server"

MOCK_DBMS = "mock"
MOCK_PLUGIN_PATH = "tests.mock_plugin:MockPlugin"
MOCK_HOST = "127.0.0.1"
MOCK_USERNAME = "mock-username"
MOCK_PASSWORD = "mock-password"

_BASE_CONFIG = {
    "host": MOCK_HOST,
    "port": 0,
    "username": MOCK_USERNAME,
    "password": MOCK_PASSWORD,
    "driver": "ignored",
    "database": "ignored",
}


def make_config(transport: str, port: int = 0) -> dict:
    return {
        **_BASE_CONFIG,
        "dbms": MOCK_DBMS,
        "transport": transport,
        "port": port,
    }


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((MOCK_HOST, 0))
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
    server.PLUGINS = {MOCK_DBMS: MOCK_PLUGIN_PATH}
    config = make_config(transport=transport, port=port)
    app = FastMCP(MOCK_SERVER_NAME, lifespan=server.app_lifespan(config))
    app.run(transport=transport, host=MOCK_HOST, port=port, show_banner=False)


@pytest.fixture()
def stdio_server(monkeypatch):
    monkeypatch.setattr(server, "PLUGINS", {MOCK_DBMS: MOCK_PLUGIN_PATH})
    return FastMCP(MOCK_SERVER_NAME, lifespan=server.app_lifespan(make_config("stdio")))


@pytest.fixture()
async def stdio_client(stdio_server):
    async with Client(stdio_server) as client:
        yield client


@pytest.fixture()
def localhost_server():
    processes: list[Process] = []

    def run_server(transport: str):
        port = _get_free_port()
        proc = Process(target=_run_server, args=(transport, port), daemon=True)
        proc.start()
        try:
            _wait_for_port(MOCK_HOST, port, proc)
            processes.append(proc)
            return _get_url(transport, MOCK_HOST, port)
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
def config_file(tmp_path):
    path = tmp_path / "conf.json"
    path.write_text(
        json.dumps(
            {
                "host": MOCK_HOST,
                "port": 1234,
                "driver": "driver-in-conf-file",
                "database": "db-in-conf-file",
            }
        )
    )
    return path