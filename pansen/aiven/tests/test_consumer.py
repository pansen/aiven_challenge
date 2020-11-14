import logging

import pytest

from pansen.aiven.consumer import url_metrics_agent
from pansen.aiven.lib.tests.test_transport import _build_response
from pansen.aiven.lib.transport import MonitorUrlMetrics

log = logging.getLogger(__name__)


@pytest.mark.asyncio()
async def test_url_metrics_agent(faust_app):
    """
    See: https://faust.readthedocs.io/en/latest/userguide/testing.html#testing-with-pytest
    """
    async with url_metrics_agent.test_context() as agent:
        mum = MonitorUrlMetrics.from_respose(_build_response())

        # We act with the `faust` agent, which is not aware of the auto-conversion that our
        # Kafka producer has. Thus we manually need to call `to_wire` here.
        event = await agent.put(mum.to_wire())

        assert agent.results[event.message.offset] == mum
        assert isinstance(MonitorUrlMetrics.from_json(event.value), MonitorUrlMetrics)
