# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

from argparse import Namespace
import json

import pytest

from actian_mcp_server.server import load_config, validate_config
from tests.conftest import MOCK_DBMS, MOCK_HOST

def test_load_config_simple(config_file):
    cli_args = Namespace(
        dbms=MOCK_DBMS,
        conf_file=str(config_file),
        transport="stdio",
        username="cli-username",
        password="cli-password",
    )

    config = load_config(cli_args)

    assert config == {
        "host": MOCK_HOST,
        "port": 1234,
        "driver": "driver-in-conf-file",
        "database": "db-in-conf-file",
        "dbms": MOCK_DBMS,
        "transport": "stdio",
        "username": "cli-username",
        "password": "cli-password",
        "max_rows": 1000
    }


def test_load_config_raises_for_missing_file(tmp_path):
    cli_args = Namespace(
        dbms=MOCK_DBMS,
        conf_file=str(tmp_path / "missing.json"),
        transport="stdio",
        username="cli-username",
        password="cli-password",
    )

    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        load_config(cli_args)


def test_load_config_raises_for_invalid_json(tmp_path):
    invalid_config = tmp_path / "invalid.json"
    invalid_config.write_text("{invalid-json")
    cli_args = Namespace(
        dbms=MOCK_DBMS,
        conf_file=str(invalid_config),
        transport="stdio",
        username="cli-username",
        password="cli-password",
    )

    with pytest.raises(json.JSONDecodeError):
        load_config(cli_args)


def test_validate_config_stdio_transport_without_host_or_port():
    validate_config(
        {
            "dbms": MOCK_DBMS,
            "transport": "stdio",
            "username": "username",
            "password": "password",
        }
    )


@pytest.mark.parametrize("transport", ["http", "sse", "streamable-http"])
def test_validate_config_net_transports_with_host_and_port(transport):
    validate_config(
        {
            "dbms": MOCK_DBMS,
            "transport": transport,
            "host": MOCK_HOST,
            "port": 1234,
            "username": "username",
            "password": "password",
        }
    )


@pytest.mark.parametrize(
    "config, expected_error",
    [
        (
            {
                "dbms": MOCK_DBMS,
                "transport": "http",
                "port": 1234,
                "username": "username",
                "password": "password",
            },
            "Missing config for transport: host",
        ),
        (
            {
                "dbms": MOCK_DBMS,
                "transport": "sse",
                "host": MOCK_HOST,
                "username": "username",
                "password": "password",
            },
            "Missing config for transport: port",
        ),
        (
            {
                "dbms": MOCK_DBMS,
                "transport": "stdio",
                "username": "username",
                "password": None,
            },
            "username and password are required",
        ),
        (
            {
                "dbms": MOCK_DBMS,
                "transport": "stdio",
                "username": None,
                "password": "password",
            },
            "username and password are required",
        ),
    ],
)
def test_validate_config_rejects_invalid_inputs(config, expected_error):
    with pytest.raises(ValueError, match=expected_error):
        validate_config(config)
