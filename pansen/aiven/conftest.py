import inspect
import os
from asyncio.selector_events import BaseSelectorEventLoop

import pytest
from aiokafka import AIOKafkaProducer
from starlette.testclient import TestClient
from vcr import VCR

from pansen.aiven.config import Config, configure
from pansen.aiven.main import app


@pytest.fixture(scope="function")
def config() -> Config:
    return configure(app)


@pytest.fixture(scope="function")
def test_client(config) -> TestClient:
    c = TestClient(app)
    return c


@pytest.fixture(scope="function")
async def asyncio_kafka_producer(config: Config, event_loop: BaseSelectorEventLoop) -> AIOKafkaProducer:
    producer = AIOKafkaProducer(loop=event_loop, bootstrap_servers=config.KAFKA_SERVER, enable_idempotence=True)
    # Get cluster layout and initial topic/partition leadership information
    await producer.start()
    try:
        yield producer
    finally:
        # Wait for all pending messages to be delivered or expire.
        await producer.stop()


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
