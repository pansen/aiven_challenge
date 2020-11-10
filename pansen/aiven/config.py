import asyncio
import os
from dataclasses import dataclass
from logging.config import dictConfig
from urllib import parse

import msgpack
from aiokafka import AIOKafkaProducer
from dotenv import load_dotenv

from pansen.aiven import PANSEN_AIVEN_PROJECT_ROOT


@dataclass
class Config:
    KAFKA_SERVER: str
    KAFKA_TOPIC: str
    URL_CONFIG_FILE: str
    POSTGRES_URL: str
    POSTGRES_CONNECTION_ARGS: dict

    async def get_kafka_producer(self, event_loop=None) -> AIOKafkaProducer:
        # https://github.com/aio-libs/aiokafka#aiokafkaproducer
        producer = AIOKafkaProducer(
            loop=event_loop and event_loop or asyncio.get_event_loop(),
            bootstrap_servers=self.KAFKA_SERVER,
            enable_idempotence=True,
            value_serializer=lambda v: msgpack.packb(v),
        )
        # Get cluster layout and initial topic/partition leadership information
        await producer.start()
        return producer


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
    for k in (
        "KAFKA_SERVER",
        "KAFKA_TOPIC",
        "POSTGRES_URL",
    ):
        locals()[k] = os.getenv(k)

    # connection string
    parsed = parse.urlparse(os.getenv("POSTGRES_URL"))
    # create a kw_args dict, which fits https://github.com/MagicStack/asyncpg#basic-usage
    locals()["POSTGRES_CONNECTION_ARGS"] = {
        "user": parsed.username,
        "password": parsed.password,
        "host": parsed.hostname,
        "port": parsed.port,
        "database": parsed.path.lstrip("/"),
    }
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
