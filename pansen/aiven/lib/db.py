import logging
from contextlib import asynccontextmanager
from uuid import UUID

from asyncpg.pool import Pool

from pansen.aiven.lib.transport import MonitorUrlMetrics

log = logging.getLogger(__name__)


@asynccontextmanager
async def connection_with_transaction(connection, *args, **kwds):
    tx = connection.transaction()
    log.debug("_transaction start: %s ...", tx)
    await tx.start()
    try:
        yield connection
    except Exception as e:
        log.error("_transaction rollback: %s: %s", tx, e, exc_info=e)
        await tx.rollback()
        raise e
    else:
        log.debug("_transaction commit: %s", tx)
        await tx.commit()


class MonitorUrlMetricsRepository:
    def __init__(self, pool: Pool):
        self.pool = pool

    async def save(self, mum: MonitorUrlMetrics) -> UUID:
        if mum.id is not None:
            raise Exception("Updating an `MonitorUrlMetrics` instance is not supported so far; id: {mum.id}")
        log.debug("Storing: %s ...", mum)
        # https://magicstack.github.io/asyncpg/current/usage.html#connection-pools
        async with self.pool.acquire() as _connection:
            async with connection_with_transaction(_connection) as conn:
                inserted = await conn.fetch(
                    f"""
                        INSERT INTO {MONITOR_URL_METRICS_TABLE} (
                            duration,
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
                mum.id = new_row_id
                log.debug("... stored with id: %s: %s.", new_row_id, mum)
                return new_row_id


MONITOR_URL_METRICS_TABLE = "monitor_url_metrics"
