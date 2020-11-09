import asyncio
import logging

import httpx

from pansen.aiven.config import configure
from pansen.aiven.lib.schedule import Schedule

log = logging.getLogger(__name__)


async def _run(schedule: Schedule):
    """
    Entry-point to have the ability to perform some application start logic.
    """
    for _schedule in schedule:
        jobs = []
        async with httpx.AsyncClient() as client:
            for job in schedule.get_jobs():
                jobs.append(job.fetch(client))
            yield await asyncio.gather(*jobs)


async def runner(schedule):
    async for jobs in _run(schedule):
        pass


def run():
    c = configure()
    schedule = Schedule(c, max_count=2)
    asyncio.run(runner(schedule))
