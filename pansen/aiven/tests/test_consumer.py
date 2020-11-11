import pytest

from pansen.aiven.consumer import yolo_agent


@pytest.mark.asyncio()
async def test_bar(faust_app):
    """
    See: https://faust.readthedocs.io/en/latest/userguide/testing.html#testing-with-pytest
    """
    async with yolo_agent.test_context() as agent:
        event = await agent.put("hey")
        assert agent.results[event.message.offset] == "heyYOLO"
