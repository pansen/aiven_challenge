import os
from urllib import parse

import pytest
from asyncpg import Connection
from asyncpg.pool import Pool
from pansen.aiven.lib.db import MonitorUrlMetricsRepository

from pansen.aiven.config import Config


def test_URL_CONFIG_FILE_is_absolute(config: Config):
    assert os.path.isabs(config.URL_CONFIG_FILE)
    assert os.path.isfile(config.URL_CONFIG_FILE)


def test_config_postgres_url_parse(config: Config):
    urlparse = parse.urlparse(config.POSTGRES_URL)
    assert urlparse.hostname
    assert urlparse.port
    assert urlparse.username
    assert urlparse.password
    assert urlparse.path.lstrip("/")

    assert urlparse.hostname == config.POSTGRES_CONNECTION_ARGS["host"]
    assert urlparse.port == config.POSTGRES_CONNECTION_ARGS["port"]
    assert urlparse.username == config.POSTGRES_CONNECTION_ARGS["user"]
    assert urlparse.password == config.POSTGRES_CONNECTION_ARGS["password"]
    assert urlparse.path.lstrip("/") == config.POSTGRES_CONNECTION_ARGS["database"]


@pytest.mark.asyncio()
async def test_connection_pool(config: Config):
    assert isinstance(await config.POSTGRES_POOL, Pool)


@pytest.mark.asyncio()
async def test_monitor_metrics_repository_patched_connection(
    monitor_metrics_repository: MonitorUrlMetricsRepository,
    pg_connection: Connection,
):
    """
    Validate the `monitor_metrics_repository` fixture is using the PG connection of our testsuite
    """
    assert isinstance(monitor_metrics_repository, MonitorUrlMetricsRepository)

    async with monitor_metrics_repository.pool.acquire() as _connection:
        # Late import to make patching work
        from pansen.aiven.lib.db import connection_with_transaction

        async with connection_with_transaction(_connection) as conn:
            assert pg_connection == conn
