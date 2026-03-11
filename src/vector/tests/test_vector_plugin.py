# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import asyncio

import pytest

from vector.plugin import VectorPlugin
from vector.tests.conftest import make_config

SERVER_MODES = ["stdio", "localhost-http", "localhost-sse", "containerized"]


def test_vector_plugin_accepts_valid_config():
	plugin = VectorPlugin(make_config("stdio"))

	assert plugin.config["dbms"] == "vector"
	assert plugin.pool is None


# TODO: Add more test cases for invalid or missing configs
def test_vector_plugin_rejects_missing_config_username():
	config = make_config("stdio")
	config["username"] = None

	with pytest.raises(ValueError, match="username"):
		VectorPlugin(config)


@pytest.mark.parametrize("server", SERVER_MODES, indirect=True)
async def test_vector_client_connection(client, server):
	await client.ping()
