import asyncio
from datetime import datetime, timezone

from sqlalchemy import or_, select

from app.database import session_factory
from app.domain import JobStatus
from app.models import Job, OutboxEvent


async def schedule_once() -> int:
    now = datetime.now(timezone.utc)
    factory = session_factory()
    released = 0
    async with factory() as session, session.begin():
        jobs = await session.scalars(
            select(Job).where(
                or_(
                    (Job.status.in_([JobStatus.SCHEDULED, JobStatus.RETRYING]))
                    & (Job.available_at <= now),
                    (Job.status == JobStatus.RUNNING) & (Job.lease_expires_at <= now),
                )
            )
        )
        for job in jobs:
            job.status = JobStatus.QUEUED
            job.lease_owner = None
            job.lease_expires_at = None
            session.add(
                OutboxEvent(
                    aggregate_id=job.id,
                    event_type="job.queued",
                    payload={"job_id": str(job.id), "queue": job.queue_name, "priority": job.priority},
                )
            )
            released += 1
    return released


async def run() -> None:
    while True:
        await schedule_once()
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(run())
