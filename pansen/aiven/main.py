import logging
from datetime import datetime

from fastapi import FastAPI
from starlette.requests import Request

from pansen.aiven.config import configure, log_config

app = FastAPI()
log = logging.getLogger(__name__)


@app.middleware("http")
async def align_possible_testclient(request: Request, call_next):
    """
    TODO andi: testclient and real clients behave differnet in headers and `path` processing.
     We do some alignment here, to have a consistent processing down the line.
    """
    if (
        not request.scope.get("raw_path", None)
        and request.headers.get("user-agent", None) == "testclient"  # noqa: W503
        and request.scope["path"] not in [r.path for r in request.app.router.routes]  # noqa: W503
    ):
        # this will become the `full_path` parameter later
        request.scope["path"] = (
            f"{request.url.components.scheme}://" f"{request.url.components.netloc}{request.url.components.path}"
        )

    return await call_next(request)


@app.middleware("http")
async def add_x_headers(request: Request, call_next):
    """
    Add some response headers to indicate our own processing.
    """
    response = await call_next(request)
    response.headers["x-pansen-processed"] = "1"
    return response


@app.get("/status")
async def root_get(request: Request):
    """
    A status endpoint, to validate the service is running.
    """
    _runtime_delta = datetime.utcnow() - app.extra["started_at"]
    _uptime = {"days": _runtime_delta.days}
    _uptime["hours"], rem = divmod(_runtime_delta.seconds, 3600)
    _uptime["minutes"], _uptime["seconds"] = divmod(rem, 60)

    return {
        **{"counters": request.app.extra["counters"]},
        **{"uptime": _uptime},
        **{"status": "OK"},
    }


def run():
    """
    Entry-point to have the ability to perform some application start logic.
    """
    c = configure(app)

    from uvicorn.main import run

    return run("pansen.aiven.main:app", host=c.HTTP_HOST, port=c.HTTP_PORT, log_config=log_config())
