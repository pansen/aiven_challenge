import logging

import faust

from pansen.aiven.lib.transport import MonitorUrlMetrics

log = logging.getLogger(__name__)
consumer_faust_app = faust.App("pansen_aiven_consumer")

# TODO andi: implement a version that incorporates a configurable `topic`
#  https://github.com/robinhood/faust/issues/300#issuecomment-525531059
topic = consumer_faust_app.topic(
    *[
        "url_metrics",
    ],
    value_type=MonitorUrlMetrics,
)


@consumer_faust_app.agent(topic)
async def url_metrics_agent(stream):
    """
    YOLO agent for demostration.
    """
    async for value in stream:  # type: MonitorUrlMetrics
        log.info("Processing %s ...", value)
        yield value


def run():
    """
    Entry-point to have the ability to perform some application start logic.
    """
    consumer_faust_app.main()
