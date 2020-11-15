import logging
from typing import AsyncGenerator

import pytest
from aiokafka import AIOKafkaProducer
from faust import App

from pansen.aiven.config import Config
from pansen.aiven.conftest import KAFKA_PARTITION, KAFKA_TEST_TOPIC
from pansen.aiven.consumer import consumer_faust_app
from pansen.aiven.lib.tests.test_transport import _build_response
from pansen.aiven.lib.transport import MonitorUrlMetrics

log = logging.getLogger(__name__)


@pytest.mark.skip("Requires patching and is in unclear state.")
@pytest.mark.asyncio
async def test_kafka_consumer_faust(
    asyncio_kafka_producer: AIOKafkaProducer,
    faust_app: App,
):
    mum = MonitorUrlMetrics.from_respose(_build_response())
    _future = await asyncio_kafka_producer.send(KAFKA_TEST_TOPIC, mum, partition=KAFKA_PARTITION)
    resp = await _future
    assert KAFKA_PARTITION == resp.partition

    _url_metrics_agent = faust_app.agents["pansen.aiven.consumer.url_metrics_agent"]

    def _on_error(*args):
        log.error("on_error: %s", args)

    # Consume messages
    async with _url_metrics_agent.test_context(on_error=_on_error) as agent:  # type AgentTestWrapper
        _res = await agent.ask()  # noqa F841
        # TODO andi: `consumer.seek_to_committed()` call is missing here, thus we gain only `None`
        # assert _res is not None
        return

    assert False, "Did not consume anything"


@pytest.fixture()
async def faust_app(config: Config) -> AsyncGenerator[App, None]:
    """
    Fixture for our Faust app.

    See: https://faust.readthedocs.io/en/latest/userguide/testing.html#testing-with-pytest

    TODO andi:
        to make this work, `faust` needs to be patched at
        `faust.agents.replies.ReplyConsumer._reply_topic`, to contain:

        ```python
        return self.app.topic(
            topic,
            partitions=1,
            # this is the change:
            replicas=self.app.conf.topic_replication_factor,
            deleting=True,
            retention=self.app.conf.reply_expires,
            value_type=ReqRepResponse,
        )
        ```

    TODO andi: check
    - https://github.com/robinhood/faust/blob/master/t/functional/test_streams.py#L19-L26
    - https://github.com/robinhood/faust/blob/01b4c0ad8390221db71751d80001b0fd879291e2/t/functional/conftest.py#L31-L49
    """
    # This applies to all properties in `Faust`
    consumer_faust_app.conf.DEFAULT_BROKER_URL = config.KAFKA_SERVER

    # Avoid
    # ```
    # kafka.errors.InvalidReplicationFactorError: [Error 38] InvalidReplicationFactorError:
    #  Cannot create topic: f-reply-e74b5305-7b45-44e0-8252-c5dc0357eead (38):
    #  Replication factor must be larger than 0.
    # ```
    # TODO andi:
    #         to make this work, `faust` needs to be patched at
    #         `faust.agents.replies.ReplyConsumer._reply_topic`
    consumer_faust_app.conf.topic_replication_factor = 1

    consumer_faust_app.finalize()
    # consumer_faust_app.conf.store = "memory://"
    consumer_faust_app.conf.store = config.KAFKA_SERVER
    consumer_faust_app.flow_control.resume()

    try:
        yield consumer_faust_app
    finally:
        # Wait for all pending messages to be delivered or expire.
        await consumer_faust_app.stop()


@pytest.mark.asyncio()
@pytest.fixture()
def event_loop():
    """
    We want `pytest` to use the same eventloop as `Faust` uses.

    See: https://stackoverflow.com/a/63362884
    """
    yield consumer_faust_app.loop
