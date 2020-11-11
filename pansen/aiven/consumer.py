import logging

import faust

log = logging.getLogger(__name__)
consumer_faust_app = faust.App("pansen_aiven_consumer")


@consumer_faust_app.agent()
async def yolo_agent(stream):
    async for value in stream:
        yield value + "YOLO"


def run():
    """
    Entry-point to have the ability to perform some application start logic.
    """
    raise NotImplementedError()
