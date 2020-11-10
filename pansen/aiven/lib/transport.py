from dataclasses import dataclass
from datetime import datetime

from dacite import from_dict
from httpx import Response
from marshmallow import fields, post_load

from pansen.aiven.lib import UjsonSchema


@dataclass(frozen=True)
class MonitorUrlMetrics:
    duration: int
    status_code: int
    url: str
    method: str
    num_bytes_downloaded: int
    issued_at: datetime

    @classmethod
    def from_respose(cls, response: Response):
        issued_at = getattr(response.request, "issued_at", None)
        return cls(
            duration=response.elapsed.microseconds,
            status_code=response.status_code,
            url=str(response.request.url),
            method=response.request.method,
            num_bytes_downloaded=response.num_bytes_downloaded,
            issued_at=issued_at,
        )

    @classmethod
    def from_json(cls, data: dict):
        return _monitor_url_metrics_schema.load(data)

    def to_json_dict(self):
        return _monitor_url_metrics_schema.dump(self)


class MonitorUrlMetricsSchema(UjsonSchema):
    """
    Schema to validate and create a `MonitorUrlMetrics`
    """

    duration = fields.Int(required=True, allow_none=False)
    status_code = fields.Int(required=False, default=-1)
    url = fields.String(required=True, allow_none=False)
    method = fields.String(required=True, allow_none=False)
    num_bytes_downloaded = fields.Int(required=False, default=-1)
    issued_at = fields.DateTime(required=False, default=datetime.fromtimestamp(0))

    @post_load
    def make_object(self, data, **kwargs) -> MonitorUrlMetrics:
        e: MonitorUrlMetrics = from_dict(data_class=MonitorUrlMetrics, data=data)
        return e


_monitor_url_metrics_schema = MonitorUrlMetricsSchema()
