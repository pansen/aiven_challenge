import pytest
from httpx import Response

from pansen.aiven.lib.schedule import Schedule
from pansen.aiven.main import _run


@pytest.mark.asyncio
async def test_run(config):
    async for res in _run(Schedule(config, max_count=1)):
        assert 2 == len(res)
        assert all(isinstance(r, Response) for r in res)
