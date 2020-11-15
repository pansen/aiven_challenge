from datetime import datetime, timedelta

from httpx import Request, Response

from pansen.aiven.lib.transport import MonitorUrlMetrics, MonitorUrlMetricsSchema


def test_transport_schema():
    schema = MonitorUrlMetricsSchema()
    mm = MonitorUrlMetrics.from_respose(_build_response())

    # Serialize
    serialized = schema.dump(mm)
    keys_to_have = sorted(
        [
            "id",
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


def _build_response() -> Response:
    utcnow = datetime.utcnow()
    response = Response(status_code=201)
    response.elapsed = timedelta(milliseconds=123)
    response.request = Request("POST", "http://a.de/b")
    setattr(response.request, "issued_at", utcnow)  # noqa B010
    return response
