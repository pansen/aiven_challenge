import asyncio
import logging

from pansen.aiven.config import configure
from pansen.aiven.lib.http import batch_fetch
from pansen.aiven.lib.schedule import Schedule
from pansen.aiven.lib.transport import MonitorUrlMetrics

log = logging.getLogger(__name__)


async def runner(schedule):
    _producer = await schedule.config.get_kafka_producer()  # noqa F841

    try:
        async for jobs in batch_fetch(schedule):
            sends = []
            for response in jobs:
                mu_metric = MonitorUrlMetrics.from_respose(response)
                log.debug("Sending to Kafka: %s ...", mu_metric)
                sends.append(_producer.send(schedule.config.KAFKA_TOPIC, mu_metric))
            await asyncio.gather(*sends)
    finally:
        await _producer.stop()


def run():
    """
    Entry-point to have the ability to perform some application start logic.
    """
    c = configure()
    schedule = Schedule(c, max_count=2)
    asyncio.run(runner(schedule))
