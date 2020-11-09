import pytest
from httpx import Response

from pansen.aiven.lib.schedule import Schedule
from pansen.aiven.main import _run


@pytest.mark.asyncio
async def test_run(config):
    res = await _run(Schedule(config))
    assert 2 == len(res)
    assert all(isinstance(r, Response) for r in res)
