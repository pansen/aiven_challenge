import asyncio
import inspect
import logging
import os
from asyncio.selector_events import BaseSelectorEventLoop

import asyncpg
import pytest
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
from asyncpg import Connection
from faust import App
from vcr import VCR

from pansen.aiven.config import Config, configure
from pansen.aiven.consumer import consumer_faust_app

log = logging.getLogger(__name__)

KAFKA_TEST_TOPIC = "kafka_topic_testing"
KAFKA_TEST_GROUP = "kafka_group_testing"
KAFKA_PARTITION = 0
MONITOR_URL_METRICS_TABLE = "monitor_url_metrics"


@pytest.fixture(scope="function")
def config() -> Config:
    os.environ["URL_CONFIG_FILE"] = "./pansen/aiven/tests/test_url_config.yaml"
    return configure()


@pytest.fixture(scope="function")
async def asyncio_kafka_producer(config: Config, event_loop: BaseSelectorEventLoop) -> AIOKafkaProducer:
    producer = await config.get_kafka_producer(event_loop)
    await _wait_topic(producer.client, KAFKA_TEST_TOPIC)

    try:
        yield producer
    finally:
        # Wait for all pending messages to be delivered or expire.
        await producer.stop()


@pytest.fixture(scope="function")
async def asyncio_kafka_consumer(config: Config, event_loop: BaseSelectorEventLoop) -> AIOKafkaConsumer:
    consumer = AIOKafkaConsumer(
        KAFKA_TEST_TOPIC,
        loop=event_loop,
        bootstrap_servers=config.KAFKA_SERVER,
        group_id=KAFKA_TEST_GROUP,
        # https://github.com/aio-libs/aiokafka/blob/f7f55b19b43b084edc844c3531a570d233d37912/tests/test_consumer.py#L34-L37
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        request_timeout_ms=300,
        value_deserializer=_unpack,
    )
    # Get cluster layout and join group
    await consumer.start()
    await consumer.seek_to_committed()
    try:
        yield consumer
    finally:
        # Will leave consumer group; perform autocommit if enabled.
        await consumer.stop()


@pytest.fixture()
async def faust_app(config: Config) -> App:
    """
    Fixture for our Faust app, only bound to memory.

    See: https://faust.readthedocs.io/en/latest/userguide/testing.html#testing-with-pytest
    """
    consumer_faust_app.finalize()
    consumer_faust_app.conf.store = "memory://"

    try:
        yield consumer_faust_app
    finally:
        await consumer_faust_app.stop()


@pytest.fixture(scope="function")
async def raw_pg_connection(config: Config) -> Connection:
    c = await asyncpg.connect(**config.POSTGRES_CONNECTION_ARGS)
    yield c
    await c.close()


@pytest.fixture(scope="function")
async def create_tables(raw_pg_connection: Connection):
    await raw_pg_connection.execute(
        """
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    """
    )

    await raw_pg_connection.execute(
        f"""
    CREATE TABLE IF NOT EXISTS {MONITOR_URL_METRICS_TABLE} (
    id UUID NOT NULL DEFAULT uuid_generate_v1() ,
    duration integer,
    status_code integer,
    -- https://stackoverflow.com/a/417184
    url varchar(2083),
    method varchar(40),
    num_bytes_downloaded integer,
    issued_at  timestamptz,
    CONSTRAINT idx_{MONITOR_URL_METRICS_TABLE}_id PRIMARY KEY ( id )
    )
    """
    )


@pytest.fixture(scope="function")
async def pg_connection(raw_pg_connection, create_tables) -> Connection:
    await raw_pg_connection.execute("""BEGIN""")
    yield raw_pg_connection
    await raw_pg_connection.execute("""ROLLBACK""")


def _build_vcr_cassette_yaml_path_from_func_using_module(function):
    return os.path.join(os.path.dirname(inspect.getfile(function)), function.__name__ + ".yaml")


cast_vcr = VCR(
    func_path_generator=_build_vcr_cassette_yaml_path_from_func_using_module,
    decode_compressed_response=True,
    # https://vcrpy.readthedocs.io/en/latest/advanced.html#filter-sensitive-data-from-the-request
    # filter_headers=['authorization'],
    # 'new_episodes' | 'once'
    record_mode="once",
)


def _unpack(v):
    log.debug("Try unpacking: %s ...", v)
    return v


async def _wait_topic(client, topic):
    """
    Stolen from
    https://github.com/aio-libs/aiokafka/blob/f7f55b19b43b084edc844c3531a570d233d37912/tests/_testutil.py#L347-L357
    """
    client.add_topic(topic)
    for _i in range(5):
        ok = await client.force_metadata_update()
        if ok:
            ok = topic in client.cluster.topics()
        if not ok:
            await asyncio.sleep(1)
        else:
            return
    raise AssertionError('No topic "{}" exists'.format(topic))
