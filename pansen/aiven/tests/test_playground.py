import pytest
from aiokafka import AIOKafkaProducer


@pytest.mark.asyncio
async def test_kafka_producer(asyncio_kafka_producer: AIOKafkaProducer):
    await asyncio_kafka_producer.send_and_wait("my_topic", b"Super message")
