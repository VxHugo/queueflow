import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.database import session_factory
from app.domain import JobStatus, Priority
from app.models import Job, JobAttempt, JobEvent, Worker
from app.repositories import CreateJob, IdempotencyConflict, JobRepository

router = APIRouter(prefix="/api/v1")


class BackoffInput(BaseModel):
    base_seconds: int = Field(default=2, ge=1, le=60)
    max_seconds: int = Field(default=300, ge=2, le=3600)


class JobInput(BaseModel):
    queue: str = Field(min_length=1, max_length=100)
    type: str = Field(min_length=1, max_length=100)
    payload: dict[str, Any]
    priority: Priority = Priority.NORMAL
    scheduled_at: datetime | None = None
    max_attempts: int = Field(default=5, ge=1, le=20)
    backoff: BackoffInput = BackoffInput()


def job_view(job: Job) -> dict[str, Any]:
    return {"id": str(job.id), "queue": job.queue_name, "type": job.job_type, "status": job.status, "priority": job.priority, "payload": job.payload, "progress": job.progress, "attempts": job.attempts, "max_attempts": job.max_attempts, "result": job.result, "last_error": job.last_error, "created_at": job.created_at, "available_at": job.available_at}


@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def create_job(data: JobInput, idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> dict[str, Any]:
    async with session_factory()() as session, session.begin():
        try:
            job, created = await JobRepository(session).create(CreateJob(queue_name=data.queue, job_type=data.type, payload=data.payload, priority=data.priority, idempotency_key=idempotency_key, max_attempts=data.max_attempts, backoff_base=data.backoff.base_seconds, backoff_max=data.backoff.max_seconds, scheduled_at=data.scheduled_at))
        except IdempotencyConflict as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        await session.flush()
        return {**job_view(job), "created": created}


@router.get("/jobs")
async def list_jobs(status_filter: JobStatus | None = Query(default=None, alias="status"), priority: Priority | None = None, limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0)) -> dict[str, Any]:
    async with session_factory()() as session:
        statement = select(Job).order_by(Job.created_at.desc()).limit(limit).offset(offset)
        if status_filter: statement = statement.where(Job.status == status_filter)
        if priority: statement = statement.where(Job.priority == priority)
        jobs = await session.scalars(statement)
        return {"items": [job_view(job) for job in jobs], "limit": limit, "offset": offset}


@router.get("/jobs/{job_id}")
async def get_job(job_id: uuid.UUID) -> dict[str, Any]:
    async with session_factory()() as session:
        job = await session.get(Job, job_id)
        if job is None: raise HTTPException(status_code=404, detail="Job not found")
        return job_view(job)


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(job_id: uuid.UUID) -> dict[str, str]:
    async with session_factory()() as session, session.begin():
        job = await session.get(Job, job_id)
        if job is None: raise HTTPException(status_code=404, detail="Job not found")
        job.cancel_requested = True
        if job.status in {JobStatus.SCHEDULED, JobStatus.QUEUED, JobStatus.RETRYING}: job.status = JobStatus.CANCELED
        return {"status": job.status}


@router.get("/jobs/{job_id}/attempts")
async def job_attempts(job_id: uuid.UUID) -> list[dict[str, Any]]:
    async with session_factory()() as session:
        attempts = await session.scalars(select(JobAttempt).where(JobAttempt.job_id == job_id).order_by(JobAttempt.attempt_number))
        return [{"number": row.attempt_number, "worker_id": row.worker_id, "status": row.status, "error": row.error_message} for row in attempts]


@router.get("/workers")
async def workers() -> list[dict[str, Any]]:
    async with session_factory()() as session:
        rows = await session.scalars(select(Worker).order_by(Worker.name))
        return [{"id": row.id, "name": row.name, "status": row.status, "active_jobs": row.active_jobs, "capacity": row.capacity, "last_heartbeat": row.last_heartbeat} for row in rows]


@router.get("/events")
async def events(limit: int = Query(default=50, ge=1, le=100)) -> list[dict[str, Any]]:
    async with session_factory()() as session:
        rows = await session.scalars(select(JobEvent).order_by(JobEvent.created_at.desc()).limit(limit))
        return [{"id": str(row.id), "job_id": str(row.job_id), "type": row.event_type, "message": row.message, "created_at": row.created_at} for row in rows]


@router.get("/metrics/summary")
async def metrics_summary() -> dict[str, int]:
    async with session_factory()() as session:
        total = await session.scalar(select(func.count()).select_from(Job))
        queued = await session.scalar(select(func.count()).select_from(Job).where(Job.status == JobStatus.QUEUED))
        running = await session.scalar(select(func.count()).select_from(Job).where(Job.status == JobStatus.RUNNING))
        return {"total": total or 0, "queued": queued or 0, "running": running or 0}
