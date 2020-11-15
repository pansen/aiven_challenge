import logging

import faust

from pansen.aiven.config import Config, configure
from pansen.aiven.lib.db import MonitorUrlMetricsRepository
from pansen.aiven.lib.transport import MonitorUrlMetrics

log = logging.getLogger(__name__)
consumer_faust_app = faust.App("pansen_aiven_consumer")

# TODO andi: implement a version that incorporates a configurable `topic`
#  https://github.com/robinhood/faust/issues/300#issuecomment-525531059
mum_topic = consumer_faust_app.topic(
    *[
        "url_metrics",
    ],
    # TODO andi: defining `MonitorUrlMetrics` as `value_type` here does no auto marshalling.
    #  We use `bytes` to take advantage of our existing serializer.
    value_type=bytes,
)


@consumer_faust_app.agent(mum_topic)
async def url_metrics_agent(stream):
    """
    `MonitorUrlMetrics` agent.
    """
    c: Config = consumer_faust_app.conf.custom_config
    repository: MonitorUrlMetricsRepository = c.get_monitor_url_metrics_repository()

    async for value in stream:  # type: bytes
        mum = MonitorUrlMetrics.from_json(value)
        log.info("Processing %s ...", value)
        new_id = await repository.save(mum)
        mum.id = new_id
        yield mum


def run():
    """
    Entry-point to have the ability to perform some application start logic.
    """
    config: Config = configure()
    consumer_faust_app.conf.custom_config = config

    # TODO andi: any useful?
    # consumer_faust_app.conf.DEFAULT_BROKER_URL = config.KAFKA_SERVER
    # consumer_faust_app.conf.broker = yarl.URL(config.KAFKA_SERVER)
    # consumer_faust_app.conf.broker_consumer = yarl.URL(config.KAFKA_SERVER)
    # consumer_faust_app.conf.broker_producer = yarl.URL(config.KAFKA_SERVER)

    return consumer_faust_app.main()
