import os
from dataclasses import dataclass
from datetime import datetime
from logging.config import dictConfig

from aiohttp.hdrs import METH_GET, METH_POST
from dotenv import load_dotenv
from fastapi import FastAPI


@dataclass
class Config:
    HTTP_HOST: str
    HTTP_PORT: int


def configure(app: FastAPI) -> Config:
    """
    Parse the ENV and prepare a `Config` instance according to that.
    """
    load_dotenv(verbose=True)

    dictConfig(log_config())

    # int
    for k in ("HTTP_PORT",):
        locals()[k] = int(os.getenv(k))
    # string
    for k in ("HTTP_HOST",):
        locals()[k] = os.getenv(k)
    # Take all local variables to the `Config` constructor, if they start uppercase
    c = Config(**{key: value for (key, value) in locals().items() if key.isupper()})

    app.extra["config"] = c
    app.extra["started_at"] = datetime.utcnow()
    app.extra["counters"] = {
        METH_POST: 0,
        METH_GET: 0,
    }

    return c


def log_config():
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s %(levelname)-5.5s [%(name)s][%(threadName)s] %(message)s"},
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "standard", "stream": "ext://sys.stderr"}
        },
        "loggers": {
            "pansen": {
                "level": "DEBUG",
                "propagate": False,
                "handlers": ["console"],
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console"],
        },
    }
