from datetime import datetime
from typing import Optional
from uuid import UUID

import faust
from httpx import Response
from marshmallow import fields, post_load

from pansen.aiven.lib import UjsonSchema


class MonitorUrlMetrics(faust.Record):
    id: Optional[UUID]
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
    def from_json(cls, data: str):
        return _monitor_url_metrics_schema.loads(data)

    def to_wire(self):
        """
        Convert this DTO to a transmittable format.

        This format needs to match the definition and encoding in our consumer,
        `pansen.aiven.consumer.url_metrics_agent`
        """
        return _monitor_url_metrics_schema.dumps(self).encode("utf-8")


class MonitorUrlMetricsSchema(UjsonSchema):
    """
    Schema to validate and create a `MonitorUrlMetrics`
    """

    id = fields.UUID(required=False, allow_none=True)
    duration = fields.Int(required=True, allow_none=False)
    status_code = fields.Int(required=False, default=-1)
    url = fields.String(required=True, allow_none=False)
    method = fields.String(required=True, allow_none=False)
    num_bytes_downloaded = fields.Int(required=False, default=-1)
    issued_at = fields.DateTime(required=False, default=datetime.fromtimestamp(0))

    @post_load
    def make_object(self, data, **kwargs) -> MonitorUrlMetrics:
        e: MonitorUrlMetrics = MonitorUrlMetrics(**data)
        return e


_monitor_url_metrics_schema = MonitorUrlMetricsSchema()
