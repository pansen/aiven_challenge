import logging

from pansen.aiven.config import configure
from pansen.aiven.lib.http import fetch_url
from pansen.aiven.lib.schedule import Schedule

log = logging.getLogger(__name__)


def run():
    """
    Entry-point to have the ability to perform some application start logic.
    """
    c = configure()
    schedule = Schedule(c)
    for job in schedule.get_jobs():
        fetch_url(job)
