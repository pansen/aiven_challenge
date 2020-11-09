import os
from dataclasses import dataclass
from logging.config import dictConfig

from dotenv import load_dotenv

from pansen.aiven import PANSEN_AIVEN_PROJECT_ROOT


@dataclass
class Config:
    KAFKA_SERVER: str
    URL_CONFIG_FILE: str


def configure() -> Config:
    """
    Parse the ENV and prepare a `Config` instance according to that.
    """
    load_dotenv(verbose=True)

    dictConfig(log_config())

    # path
    for k in ("URL_CONFIG_FILE",):
        locals()[k] = os.path.join(PANSEN_AIVEN_PROJECT_ROOT, os.getenv(k))

    # string
    for k in ("KAFKA_SERVER",):
        locals()[k] = os.getenv(k)
    # Take all local variables to the `Config` constructor, if they start uppercase
    c = Config(**{key: value for (key, value) in locals().items() if key.isupper()})

    import logging

    logging.getLogger(__name__).debug("Config: %s", c)
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
            "level": "DEBUG",
            "handlers": ["console"],
        },
    }
