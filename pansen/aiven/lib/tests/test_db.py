import pytest
from asyncpg import Connection
from asyncpg.protocol.protocol import Record

from pansen.aiven.lib.db import MONITOR_URL_METRICS_TABLE, MonitorUrlMetricsRepository
from pansen.aiven.lib.tests.test_transport import _build_response
from pansen.aiven.lib.transport import MonitorUrlMetrics


@pytest.mark.asyncio
async def test_transport_monitor_url_metrics_save(
    monitor_metrics_repository: MonitorUrlMetricsRepository, pg_connection: Connection
):
    mum = MonitorUrlMetrics.from_respose(_build_response())

    # Insert a record into the created table.
    new_row_id = await monitor_metrics_repository.save(mum)

    row = await pg_connection.fetchrow(
        f"""
    SELECT * FROM {MONITOR_URL_METRICS_TABLE} WHERE id = $1
    """,
        new_row_id,
    )
    assert row is not None
    assert isinstance(row, Record)
