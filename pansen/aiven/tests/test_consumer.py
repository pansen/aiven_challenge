import logging
from copy import deepcopy

import pytest
from asyncpg import Connection, Record

from pansen.aiven.consumer import url_metrics_agent
from pansen.aiven.lib.db import MONITOR_URL_METRICS_TABLE
from pansen.aiven.lib.tests.test_transport import _build_response
from pansen.aiven.lib.transport import MonitorUrlMetrics

log = logging.getLogger(__name__)


@pytest.mark.asyncio()
async def test_url_metrics_agent(faust_app, pg_connection: Connection):
    """
    See: https://faust.readthedocs.io/en/latest/userguide/testing.html#testing-with-pytest
    """

    len_before = len(
        await pg_connection.fetch(
            f"""
    SELECT * FROM {MONITOR_URL_METRICS_TABLE}
    """
        )
    )

    async with url_metrics_agent.test_context() as agent:
        mum = MonitorUrlMetrics.from_respose(_build_response())
        event = await agent.put(mum)
        return_mum = agent.results[event.message.offset]

        _mum_copy = deepcopy(mum)
        _mum_copy.id = return_mum.id
        assert return_mum == _mum_copy
        assert isinstance(event.value, MonitorUrlMetrics)

        assert len_before + 1 == len(
            await pg_connection.fetch(
                f"""
        SELECT * FROM {MONITOR_URL_METRICS_TABLE}
        """
            )
        )

        row = await pg_connection.fetchrow(
            f"""
        SELECT * FROM {MONITOR_URL_METRICS_TABLE} WHERE id = $1
        """,
            return_mum.id,
        )
        assert row is not None
        assert isinstance(row, Record)

        assert isinstance(MonitorUrlMetrics.from_json(dict(row)), MonitorUrlMetrics)
