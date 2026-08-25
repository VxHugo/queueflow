import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


class RetryableJobError(RuntimeError):
    pass


ProgressReporter = Callable[[int], Awaitable[None]]
CancellationCheck = Callable[[], Awaitable[bool]]


async def demo_sleep(
    payload: dict[str, Any], report_progress: ProgressReporter, is_canceled: CancellationCheck
) -> dict[str, Any]:
    seconds = min(max(int(payload.get("seconds", 1)), 1), 300)
    for current in range(seconds):
        if await is_canceled():
            raise asyncio.CancelledError("Job cancellation was requested")
        await asyncio.sleep(1)
        await report_progress(round((current + 1) / seconds * 100))
    return {"slept_seconds": seconds}


async def demo_fail(payload: dict[str, Any], attempt: int) -> dict[str, Any]:
    if payload.get("permanent") or attempt <= int(payload.get("failures", 0)):
        raise RetryableJobError("Configured demonstration failure")
    return {"attempt": attempt, "outcome": "succeeded"}


async def execute_handler(
    job_type: str,
    payload: dict[str, Any],
    attempt: int,
    report_progress: ProgressReporter,
    is_canceled: CancellationCheck,
) -> dict[str, Any]:
    if job_type == "demo.sleep":
        return await demo_sleep(payload, report_progress, is_canceled)
    if job_type == "demo.fail":
        return await demo_fail(payload, attempt)
    raise ValueError(f"Unsupported job type: {job_type}")
