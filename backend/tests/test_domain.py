import pytest

from app.domain import InvalidStateTransition, JobStatus, ensure_transition, payload_hash


def test_payload_hash_is_stable_for_equivalent_json() -> None:
    assert payload_hash({"width": 1280, "format": "webp"}) == payload_hash(
        {"format": "webp", "width": 1280}
    )


def test_lifecycle_allows_retry_to_queue() -> None:
    ensure_transition(JobStatus.RETRYING, JobStatus.QUEUED)


def test_lifecycle_rejects_terminal_transition() -> None:
    with pytest.raises(InvalidStateTransition):
        ensure_transition(JobStatus.SUCCEEDED, JobStatus.QUEUED)
