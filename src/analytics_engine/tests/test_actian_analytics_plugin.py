# Copyright (C) 2025 Actian Corp.
# All Rights Reserved.

import pytest

from analytics_engine.plugin import AnalyticsEnginePlugin
from analytics_engine.tests.conftest import make_config

SERVER_MODES = ["stdio", "localhost-http", "localhost-sse", "containerized"]


def test_analytics_engine_plugin_accepts_valid_config():
	plugin = AnalyticsEnginePlugin(make_config("stdio"))

	assert plugin.config["dbms"] == "analytics_engine"
	assert plugin.pool is None


# TODO: Add more test cases for invalid or missing configs
def test_analytics_engine_plugin_rejects_missing_config_username():
	config = make_config("stdio")
	config["username"] = None

	with pytest.raises(ValueError, match="username"):
		AnalyticsEnginePlugin(config)


@pytest.mark.parametrize("server", SERVER_MODES, indirect=True)
async def test_analytics_engine_client_connection(client, server):
	await client.ping()
