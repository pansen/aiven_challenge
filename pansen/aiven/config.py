import asyncio
import os
from dataclasses import dataclass
from logging.config import dictConfig
from typing import Optional
from urllib import parse

import asyncpg
from aiokafka import AIOKafkaProducer
from asyncpg import Connection
from asyncpg.pool import Pool
from dotenv import load_dotenv

from pansen.aiven import PANSEN_AIVEN_PROJECT_ROOT
from pansen.aiven.lib.db import MONITOR_URL_METRICS_TABLE, MonitorUrlMetricsRepository, connection_with_transaction
from pansen.aiven.lib.transport import MonitorUrlMetrics


@dataclass
class Config:
    KAFKA_SERVER: str
    KAFKA_TOPIC: str
    URL_CONFIG_FILE: str
    POSTGRES_URL: str
    POSTGRES_CONNECTION_ARGS: dict
    _POSTGRES_POOL: Optional[Pool] = None

    @property
    async def POSTGRES_POOL(self) -> Pool:
        if self._POSTGRES_POOL:
            return self._POSTGRES_POOL
        self._POSTGRES_POOL = await asyncpg.create_pool(**self.POSTGRES_CONNECTION_ARGS)

        # TODO andi: not something I would do automatically, there are tools like 'Alembic' and
        #  this should be triggered explicitly. Yet for the sake of this exercise it's fine
        #  to call it automatically (also because there is no harm).
        async with self._POSTGRES_POOL.acquire() as _connection:
            async with connection_with_transaction(_connection) as conn:
                await self.create_tables(conn)

        return self._POSTGRES_POOL

    async def get_kafka_producer(self, event_loop=None) -> AIOKafkaProducer:
        def _serializer(v):
            if isinstance(v, MonitorUrlMetrics):
                return v.to_wire()
            raise NotImplementedError(f"Value-type {type(v)} is not implemented.")

        # https://github.com/aio-libs/aiokafka#aiokafkaproducer
        producer = AIOKafkaProducer(
            loop=event_loop and event_loop or asyncio.get_event_loop(),
            bootstrap_servers=self.KAFKA_SERVER,
            enable_idempotence=True,
            value_serializer=_serializer,
        )
        # Get cluster layout and initial topic/partition leadership information
        await producer.start()
        return producer

    async def get_monitor_url_metrics_repository(self) -> MonitorUrlMetricsRepository:
        return MonitorUrlMetricsRepository(await self.POSTGRES_POOL)

    async def create_tables(self, pg_connection: Connection):
        import logging

        log = logging.getLogger(__name__)
        log.info("Create extension `uuid-ossp` ...")
        await pg_connection.execute(
            """
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        """
        )

        log.info("Create table `%s` ...", MONITOR_URL_METRICS_TABLE)
        await pg_connection.execute(
            f"""
        CREATE TABLE IF NOT EXISTS {MONITOR_URL_METRICS_TABLE} (
        id UUID NOT NULL DEFAULT uuid_generate_v1() ,
        duration integer,
        status_code integer,
        -- https://stackoverflow.com/a/417184
        url varchar(2083),
        method varchar(40),
        num_bytes_downloaded integer,
        issued_at  timestamptz,
        CONSTRAINT idx_{MONITOR_URL_METRICS_TABLE}_id PRIMARY KEY ( id )
        )
        """
        )


def configure() -> Config:
    """
    Parse the ENV and prepare a `Config` instance according to that.
    """
    load_dotenv(verbose=True)

    dictConfig(log_config())

    # path
    for k in ("URL_CONFIG_FILE",):
        locals()[k] = os.path.join(PANSEN_AIVEN_PROJECT_ROOT, os.getenv(k))  # type: ignore

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
        "database": parsed.path.lstrip("/"),  # type: ignore
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
            "aiokafka.conn": {
                "level": "INFO",
                "propagate": False,
                "handlers": ["console"],
            },
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["console"],
        },
    }
