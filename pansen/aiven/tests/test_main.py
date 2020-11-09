from unittest import mock

import pytest
from httpx import Response

from pansen.aiven.config import Config
from pansen.aiven.lib.schedule import Schedule
from pansen.aiven.lib.http import batch_fetch
from pansen.aiven.main import runner


@pytest.mark.asyncio
async def test_batch_fetch(config, asyncio_kafka_producer):
    async for jobs in batch_fetch(Schedule(config, max_count=1)):
        assert 2 == len(jobs)
        assert all(isinstance(r, Response) for r in jobs)


@pytest.mark.asyncio
async def test_runner(config, asyncio_kafka_producer):
    with mock.patch.object(
        Config, "get_kafka_producer", return_value=asyncio_kafka_producer
    ) as _m_kafka_producer:  # noqa F841
        await runner(Schedule(config, max_count=1))
