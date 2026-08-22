from collections.abc import Awaitable, Callable

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


async def check_dependencies(database: AsyncEngine, redis: Redis) -> dict[str, bool]:
    async def check_database() -> bool:
        async with database.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True

    async def check_redis() -> bool:
        return bool(await redis.ping())

    checks: dict[str, Callable[[], Awaitable[bool]]] = {
        "postgres": check_database,
        "redis": check_redis,
    }
    results: dict[str, bool] = {}
    for name, check in checks.items():
        try:
            results[name] = await check()
        except Exception:
            results[name] = False
    return results

