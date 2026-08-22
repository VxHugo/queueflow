from unittest.mock import AsyncMock, MagicMock

import pytest

from app.health import check_dependencies


@pytest.mark.asyncio
async def test_dependency_check_reports_healthy_services() -> None:
    connection = MagicMock()
    connection.execute = AsyncMock()
    database = MagicMock()
    database.connect.return_value.__aenter__ = AsyncMock(return_value=connection)
    database.connect.return_value.__aexit__ = AsyncMock(return_value=None)
    redis = MagicMock()
    redis.ping = AsyncMock(return_value=True)

    assert await check_dependencies(database, redis) == {"postgres": True, "redis": True}


@pytest.mark.asyncio
async def test_dependency_check_reports_unavailable_service() -> None:
    database = MagicMock()
    database.connect.side_effect = RuntimeError("database unavailable")
    redis = MagicMock()
    redis.ping = AsyncMock(return_value=True)

    assert await check_dependencies(database, redis) == {"postgres": False, "redis": True}
