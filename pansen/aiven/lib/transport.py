from dataclasses import dataclass

from httpx import Response


@dataclass(frozen=True)
class MonitorUrlMetrics:
    duration: int
    url: str
    method: str

    @classmethod
    def from_respose(cls, response: Response):
        return cls(
            duration=response.elapsed.microseconds, url=str(response.request.url), method=response.request.method
        )
