from datetime import datetime, timedelta

import pytest
from asyncpg import Connection
from asyncpg.protocol.protocol import Record
from httpx import Request, Response

from pansen.aiven.conftest import MONITOR_URL_METRICS_TABLE
from pansen.aiven.lib.transport import MonitorUrlMetrics, MonitorUrlMetricsSchema


def test_transport_schema():
    schema = MonitorUrlMetricsSchema()
    mm = MonitorUrlMetrics.from_respose(_build_response())

    # Serialize
    serialized = schema.dump(mm)
    keys_to_have = sorted(
        [
            "url",
            "issued_at",
            "status_code",
            "num_bytes_downloaded",
            "duration",
            "method",
        ]
    )
    assert keys_to_have == sorted(list(serialized.keys()))
    assert str == type(serialized["issued_at"])  # noqa E721

    # Deserialize
    mm_deserialized = schema.load(serialized)
    assert isinstance(mm_deserialized, MonitorUrlMetrics)
    assert isinstance(mm_deserialized.issued_at, datetime)

    mm_deserialized = MonitorUrlMetrics.from_json(schema.dumps(mm))
    assert isinstance(mm_deserialized, MonitorUrlMetrics)
    assert isinstance(mm_deserialized.issued_at, datetime)


@pytest.mark.asyncio
async def test_transport_entity_is_persistable(pg_connection: Connection):
    mm = MonitorUrlMetrics.from_respose(_build_response())

    # Insert a record into the created table.
    inserted = await pg_connection.fetch(
        f"""
        INSERT INTO {MONITOR_URL_METRICS_TABLE} (
            duration ,
            status_code,
            url,
            method,
            num_bytes_downloaded,
            issued_at
            )
        VALUES($1, $2, $3, $4, $5, $6 )
        RETURNING id
    """,
        mm.duration,
        mm.status_code,
        mm.url,
        mm.method,
        mm.num_bytes_downloaded,
        mm.issued_at,
    )
    new_row_id = str(inserted[0][0])

    row = await pg_connection.fetchrow(
        f"""
    SELECT * FROM {MONITOR_URL_METRICS_TABLE} WHERE id = $1
    """,
        new_row_id,
    )
    assert row is not None
    assert isinstance(row, Record)


def _build_response() -> Response:
    utcnow = datetime.utcnow()
    response = Response(status_code=201)
    response.elapsed = timedelta(milliseconds=123)
    response.request = Request("POST", "http://a.de/b")
    setattr(response.request, "issued_at", utcnow)  # noqa B010
    return response
