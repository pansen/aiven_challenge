import logging
from uuid import UUID

from asyncpg import Connection
from asyncpg.pool import Pool

from pansen.aiven.lib.transport import MonitorUrlMetrics

log = logging.getLogger(__name__)


class MonitorUrlMetricsRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def save(self, mum: MonitorUrlMetrics) -> UUID:
        if mum.id is not None:
            raise Exception("Updating an `MonitorUrlMetrics` instance is not supported so far; id: {mum.id}")
        log.debug("Storing: %s ...", mum)
        async for t in self._transaction():
            # Insert a record into the created table.
            inserted = await t.fetch(
                f"""
                    INSERT INTO {MONITOR_URL_METRICS_TABLE} (
                        duration ,
                        status_code,
                        url,
                        method,
                        num_bytes_downloaded,
                        issued_at
                        )
                    VALUES($1, $2, $3, $4, $5, $6 )
                    RETURNING id
                """,
                mum.duration,
                mum.status_code,
                mum.url,
                mum.method,
                mum.num_bytes_downloaded,
                mum.issued_at,
            )
            new_row_id = UUID(str(inserted[0][0]))
            log.debug("... stored: %s with id: %s ...", mum, new_row_id)
            # TODO andi: `async generator ignored GeneratorExit`
            return new_row_id
        raise Exception("Invalid")

    async def _transaction(self) -> Connection:
        """
        Transaction providing coroutine, since this is `async` and we cannot `yield from` in an
        async function.

        This method exists for convenience in our class and to allow patching this method with a
        non-transactional `Connection` during tests.
        """
        # https://magicstack.github.io/asyncpg/current/usage.html#connection-pools
        connection = await self.pool.acquire()
        async with connection.transaction():
            yield connection


MONITOR_URL_METRICS_TABLE = "monitor_url_metrics"
