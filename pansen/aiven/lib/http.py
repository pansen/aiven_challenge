import logging
from dataclasses import dataclass
from typing import Optional

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class MonitorUrlJob:
    """
    Entity to represent a URL check configuration.
    """

    method: str
    url: str
    headers: Optional[dict]
    body: Optional[dict]

    async def fetch(self, client):
        log.debug("Issuing: %s ...", self)
        return await client.request(self.method.lower(), self.url, headers=self.headers, json=self.body)
