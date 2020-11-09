import asyncio
import logging

import msgpack
from aiokafka import AIOKafkaProducer

from pansen.aiven.config import configure
from pansen.aiven.lib.http import batch_fetch
from pansen.aiven.lib.schedule import Schedule

log = logging.getLogger(__name__)


async def runner(schedule):
    producer = AIOKafkaProducer(
        loop=asyncio.get_event_loop(),
        bootstrap_servers=schedule.config.KAFKA_SERVER,
        enable_idempotence=True,
        value_serializer=lambda v: msgpack.packb(v),
    )
    # Get cluster layout and initial topic/partition leadership information
    await producer.start()

    async for jobs in batch_fetch(schedule):
        pass


def run():
    """
    Entry-point to have the ability to perform some application start logic.
    """
    c = configure()
    schedule = Schedule(c, max_count=2)
    asyncio.run(runner(schedule))
