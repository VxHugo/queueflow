import pytest

from app.handlers import RetryableJobError, demo_fail


@pytest.mark.asyncio
async def test_demo_fail_succeeds_after_configured_failures() -> None:
    with pytest.raises(RetryableJobError):
        await demo_fail({"failures": 1}, attempt=1)
    assert await demo_fail({"failures": 1}, attempt=2) == {"attempt": 2, "outcome": "succeeded"}
