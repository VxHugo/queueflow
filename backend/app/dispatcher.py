import asyncio
from datetime import datetime, timezone

from redis.asyncio import from_url
from sqlalchemy import select

from app.database import session_factory
from app.domain import Priority
from app.models import OutboxEvent
from app.priority import stream_name
from app.settings import get_settings


async def dispatch_once() -> int:
    factory = session_factory()
    redis = from_url(get_settings().redis_url, decode_responses=True)
    count = 0
    try:
        async with factory() as session, session.begin():
            events = await session.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.published_at.is_(None))
                .order_by(OutboxEvent.created_at)
                .with_for_update(skip_locked=True)
                .limit(100)
            )
            for event in events:
                priority = Priority(event.payload.get("priority", Priority.NORMAL))
                await redis.xadd(stream_name(priority), {"event_id": str(event.id), **event.payload})
                event.published_at = datetime.now(timezone.utc)
                event.publish_attempts += 1
                count += 1
        return count
    finally:
        await redis.aclose()


async def run() -> None:
    while True:
        await dispatch_once()
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(run())
