import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx
from httpx import AsyncClient

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class MonitorUrlJob:
    """
    Entity to represent a URL check configuration.
    """

    method: str
    url: str
    headers: Optional[dict]
    body: Optional[dict]

    async def fetch(self, client: AsyncClient):
        log.debug("Issuing: %s ...", self)
        utcnow = datetime.utcnow()
        response = await client.request(self.method.lower(), self.url, headers=self.headers, json=self.body)
        setattr(response.request, "issued_at", utcnow)  # noqa B010
        return response


async def batch_fetch(schedule):
    """
    @type schedule: pansen.aiven.lib.schedule.Schedule
    """
    for _schedule in schedule:
        jobs = []
        async with httpx.AsyncClient() as client:
            for job in schedule.get_jobs():
                jobs.append(job.fetch(client))
            yield await asyncio.gather(*jobs)
