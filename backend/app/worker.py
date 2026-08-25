import asyncio
import os
import random
from datetime import datetime, timedelta, timezone

from redis.asyncio import from_url
from sqlalchemy import select

from app.database import session_factory
from app.domain import JobStatus
from app.handlers import RetryableJobError, execute_handler
from app.models import Job, JobAttempt, Worker
from app.priority import stream_name, weighted_priority_cycle
from app.settings import get_settings


class WorkerService:
    def __init__(self, worker_id: str) -> None:
        self.worker_id = worker_id
        self.redis = from_url(get_settings().redis_url, decode_responses=True)
        self.sessions = session_factory()
        self.streams = weighted_priority_cycle()

    async def start(self) -> None:
        async with self.sessions() as session, session.begin():
            worker = await session.get(Worker, self.worker_id)
            if worker is None:
                session.add(Worker(id=self.worker_id, name=self.worker_id, status="ONLINE", hostname=os.getenv("HOSTNAME", self.worker_id), capacity=1, version="0.1.0", metadata_={}))
        for priority in set(self.streams):
            try:
                await self.redis.xgroup_create(stream_name(priority), "queueflow-workers", id="0", mkstream=True)
            except Exception as error:
                if "BUSYGROUP" not in str(error):
                    raise

    async def heartbeat(self) -> None:
        async with self.sessions() as session, session.begin():
            worker = await session.get(Worker, self.worker_id)
            if worker:
                worker.last_heartbeat = datetime.now(timezone.utc)
                worker.status = "ONLINE"

    async def run_once(self) -> bool:
        priority = self.streams[0]
        self.streams.rotate(-1)
        stream = stream_name(priority)
        messages = await self.redis.xreadgroup("queueflow-workers", self.worker_id, {stream: ">"}, count=1, block=1000)
        if not messages:
            await self.heartbeat()
            return False
        _, entries = messages[0]
        message_id, values = entries[0]
        await self.process(values["job_id"])
        await self.redis.xack(stream, "queueflow-workers", message_id)
        return True

    async def process(self, job_id: str) -> None:
        async with self.sessions() as session, session.begin():
            job = await session.scalar(select(Job).where(Job.id == job_id).with_for_update())
            if job is None or job.cancel_requested:
                return
            job.status = JobStatus.RUNNING
            job.attempts += 1
            job.lease_owner = self.worker_id
            job.lease_expires_at = datetime.now(timezone.utc) + timedelta(seconds=30)
            attempt = JobAttempt(job_id=job.id, attempt_number=job.attempts, worker_id=self.worker_id, status="RUNNING")
            session.add(attempt)
            await session.flush()
            try:
                async def report(progress: int) -> None:
                    job.progress = progress

                async def canceled() -> bool:
                    await session.refresh(job)
                    return job.cancel_requested

                job.result = await execute_handler(job.job_type, job.payload, job.attempts, report, canceled)
                job.status = JobStatus.SUCCEEDED
                job.progress = 100
                job.completed_at = datetime.now(timezone.utc)
                attempt.status = "SUCCEEDED"
            except asyncio.CancelledError:
                job.status = JobStatus.CANCELED
                attempt.status = "CANCELED"
            except RetryableJobError as error:
                job.status = (
                    JobStatus.RETRYING
                    if job.attempts < job.max_attempts
                    else JobStatus.DEAD_LETTERED
                )
                if job.status == JobStatus.RETRYING:
                    limit = min(job.backoff_max, job.backoff_base * 2 ** (job.attempts - 1))
                    job.available_at = datetime.now(timezone.utc) + timedelta(
                        seconds=random.uniform(0, limit)
                    )
                job.last_error = {"type": type(error).__name__, "message": str(error)}
                attempt.status = "FAILED"
            finally:
                attempt.finished_at = datetime.now(timezone.utc)
                job.lease_owner = None
                job.lease_expires_at = None

    async def close(self) -> None:
        await self.redis.aclose()


async def run() -> None:
    service = WorkerService(os.getenv("WORKER_ID", "worker-local"))
    await service.start()
    try:
        while True:
            await service.run_once()
    finally:
        await service.close()


if __name__ == "__main__":
    asyncio.run(run())
