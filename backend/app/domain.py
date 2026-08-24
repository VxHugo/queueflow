import hashlib
import json
from enum import StrEnum


class JobStatus(StrEnum):
    SCHEDULED = "SCHEDULED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    RETRYING = "RETRYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    DEAD_LETTERED = "DEAD_LETTERED"
    CANCELED = "CANCELED"


class Priority(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    NORMAL = "NORMAL"
    LOW = "LOW"


ALLOWED_TRANSITIONS: dict[JobStatus, set[JobStatus]] = {
    JobStatus.SCHEDULED: {JobStatus.QUEUED, JobStatus.CANCELED},
    JobStatus.QUEUED: {JobStatus.RUNNING, JobStatus.CANCELED},
    JobStatus.RUNNING: {
        JobStatus.SUCCEEDED,
        JobStatus.RETRYING,
        JobStatus.DEAD_LETTERED,
        JobStatus.CANCELED,
    },
    JobStatus.RETRYING: {JobStatus.QUEUED, JobStatus.CANCELED},
    JobStatus.DEAD_LETTERED: {JobStatus.QUEUED},
    JobStatus.SUCCEEDED: set(),
    JobStatus.FAILED: set(),
    JobStatus.CANCELED: set(),
}


class InvalidStateTransition(ValueError):
    pass


def ensure_transition(current: JobStatus, target: JobStatus) -> None:
    if target not in ALLOWED_TRANSITIONS[current]:
        raise InvalidStateTransition(f"Cannot transition job from {current} to {target}")


def payload_hash(payload: dict[str, object]) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(normalized.encode()).hexdigest()

