import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import JobStatus, Priority, payload_hash
from app.models import Job, JobEvent, OutboxEvent


class IdempotencyConflict(ValueError):
    pass


@dataclass(frozen=True)
class CreateJob:
    queue_name: str
    job_type: str
    payload: dict[str, Any]
    priority: Priority = Priority.NORMAL
    idempotency_key: str | None = None
    max_attempts: int = 5
    backoff_base: int = 2
    backoff_max: int = 300
    scheduled_at: datetime | None = None


class JobRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, command: CreateJob) -> tuple[Job, bool]:
        request_hash = payload_hash(command.payload)
        status = JobStatus.SCHEDULED if command.scheduled_at else JobStatus.QUEUED
        job = Job(
            id=uuid.uuid4(),
            queue_name=command.queue_name, job_type=command.job_type, payload=command.payload,
            payload_hash=request_hash, priority=command.priority, status=status,
            idempotency_key=command.idempotency_key, max_attempts=command.max_attempts,
            backoff_base=command.backoff_base, backoff_max=command.backoff_max,
            scheduled_at=command.scheduled_at, available_at=command.scheduled_at,
        )
        if command.idempotency_key is None:
            await self._add_new_job_records(job)
            return job, True
        try:
            async with self.session.begin_nested():
                await self._add_new_job_records(job)
                await self.session.flush()
        except IntegrityError:
            existing = await self._get_by_key(command.queue_name, command.idempotency_key)
            if existing is None:
                raise
            if existing.payload_hash != request_hash:
                raise IdempotencyConflict("Idempotency key was already used with a different payload")
            return existing, False
        return job, True

    async def _add_new_job_records(self, job: Job) -> None:
        self.session.add(job)
        self.session.add(JobEvent(job_id=job.id, event_type="job.created", message="Job persisted", metadata_={"status": job.status, "priority": job.priority}))
        self.session.add(OutboxEvent(aggregate_id=job.id, event_type="job.queued", payload={"job_id": str(job.id), "queue": job.queue_name, "priority": job.priority}))

    async def _get_by_key(self, queue_name: str, key: str) -> Job | None:
        statement = select(Job).where(Job.queue_name == queue_name, Job.idempotency_key == key)
        return await self.session.scalar(statement)
