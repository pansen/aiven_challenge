import asyncio
import logging
from typing import Optional

import click

from pansen.aiven.config import configure
from pansen.aiven.lib.http import batch_fetch
from pansen.aiven.lib.schedule import Schedule
from pansen.aiven.lib.transport import MonitorUrlMetrics

log = logging.getLogger(__name__)


async def runner(schedule: Optional[Schedule] = None, max_count=2):
    if not schedule:
        c = configure()
        schedule = Schedule(c, max_count=max_count)
    _producer = await schedule.config.get_kafka_producer()  # noqa F841

    try:
        async for jobs in batch_fetch(schedule):
            # https://aiokafka.readthedocs.io/en/stable/producer.html#direct-batch-control
            batch = _producer.create_batch()
            for response in jobs:
                mu_metric = MonitorUrlMetrics.from_respose(response)
                log.debug("Sending to Kafka: %s ...", mu_metric)
                metadata = batch.append(value=mu_metric.to_wire(), key=None, timestamp=None)
                if metadata is None:
                    raise Exception(f"Found no metadata to add: {mu_metric.to_wire()}")
            _fut = await _producer.send_batch(batch, schedule.config.KAFKA_TOPIC, partition=None)
            _record = await _fut  # noqa F841
    finally:
        await _producer.stop()


@click.command()
@click.help_option("-h", "--help")
@click.option(
    "-c", "--count", default=2, required=False, show_default=True, help="How many iterations to run the schedule."
)
def run(count):
    """
    Entry-point to have the ability to perform some application start logic.
    """
    asyncio.run(runner(max_count=count))
