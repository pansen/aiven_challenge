import pytest
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from aiokafka.structs import RecordMetadata
from asyncpg import Connection
from kafka import TopicPartition

from pansen.aiven.config import Config
from pansen.aiven.conftest import KAFKA_PARTITION, KAFKA_TEST_TOPIC


@pytest.mark.asyncio
async def test_kafka_producer(asyncio_kafka_producer: AIOKafkaProducer):
    res = await asyncio_kafka_producer.send_and_wait(KAFKA_TEST_TOPIC, {"a": 1})
    assert isinstance(res, RecordMetadata)


@pytest.mark.asyncio
async def test_kafka_consumer_partition(asyncio_kafka_consumer: AIOKafkaConsumer):
    assert [
        TopicPartition(KAFKA_TEST_TOPIC, KAFKA_PARTITION),
    ] == sorted(list(asyncio_kafka_consumer.assignment()))


@pytest.mark.asyncio
async def test_kafka_consumer_consume(
    asyncio_kafka_producer: AIOKafkaProducer, asyncio_kafka_consumer: AIOKafkaConsumer
):
    _future = await asyncio_kafka_producer.send(KAFKA_TEST_TOPIC, {"a": 1}, partition=KAFKA_PARTITION)
    resp = await _future
    assert KAFKA_PARTITION == resp.partition
    await asyncio_kafka_consumer.seek_to_committed()

    # Consume messages
    async for msg in asyncio_kafka_consumer:
        print("consumed: ", msg.topic, msg.partition, msg.offset, msg.key, msg.value, msg.timestamp)
        return

    assert False, "Did not consume anything"


@pytest.mark.asyncio
async def test_basic_asyncpg(config: Config, pg_connection: Connection):
    values = await pg_connection.fetch(
        """
    SELECT *
    FROM pg_catalog.pg_tables
    WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
    """
    )
    assert list == type(values)
    assert "monitor_url_metrics" == values[0]["tablename"]
