import logging
from typing import List

import yaml
from aiohttp.hdrs import METH_DELETE, METH_GET, METH_HEAD, METH_PATCH, METH_POST, METH_PUT
from dacite import from_dict
from marshmallow import fields, post_load
from marshmallow.validate import ContainsNoneOf

from pansen.aiven.config import Config
from pansen.aiven.lib import UjsonSchema
from pansen.aiven.lib.http import MonitorUrlJob

log = logging.getLogger(__name__)


class Schedule:
    """
    Entity, which represents a schedule to run 0..n `MonitorUrlJob`s according to the URL check
    configuration.

    For the sake of simplicity, this schedule implementation always fetches *all* URL check
    configurations, which are configured. For more real-world usecases, this should be a class, which
    filters URL check configurations and selectively creates `MonitorUrlJob`s.
    """

    def __init__(self, config: Config, max_count=None, wait_between=None):
        self.config = config
        self.max_count = max_count
        self.wait_between = wait_between

    def __iter__(self):
        self._count = 0
        return self

    def __next__(self):
        self._count = self._count + 1
        if self.max_count == 0 or (self.max_count and self._count > self.max_count):
            raise StopIteration
        # TODO andi: add optional wait here, if `self.wait_between` is set
        return self

    def get_jobs(self) -> List[MonitorUrlJob]:
        return ScheduleSchema().load(self._parse_config())["schedule"]

    def _parse_config(self):
        with open(self.config.URL_CONFIG_FILE, "rb") as f:
            return yaml.safe_load(f)


class MonitorUrlJobSchema(UjsonSchema):
    """
    Schema to validate and create a `MonitorUrlJob`
    """

    method = fields.String(
        required=False,
        missing=METH_GET,
        validate=ContainsNoneOf([METH_GET, METH_POST, METH_PUT, METH_HEAD, METH_PATCH, METH_DELETE]),
    )
    url = fields.String(required=True, allow_none=False)
    body = fields.Dict(required=False, missing=None)
    headers = fields.Dict(required=False, missing=None)

    @post_load
    def make_object(self, data, **kwargs) -> MonitorUrlJob:
        e: MonitorUrlJob = from_dict(data_class=MonitorUrlJob, data=data)
        return e


class ScheduleSchema(UjsonSchema):
    """
    Parent schema, only exists to provide a wrapper for our yaml structure to pass to
    `MonitorUrlJobSchema`s.
    """

    schedule = fields.Nested(MonitorUrlJobSchema, many=True)
