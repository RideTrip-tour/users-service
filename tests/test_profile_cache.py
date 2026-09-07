from unittest.mock import MagicMock

import pytest

from app.services.profile_cache import ProfileIDManager


@pytest.mark.asyncio
async def test_get_profile_id_returns_cached_value(
    redis_client,
    monkeypatch,
):
    redis_client.data["profile_service:profile_id:7"] = "1"

    async def mock_get_profile_id_by_user_id(*args, **kwargs):
        pytest.fail("Database should not be called")

    monkeypatch.setattr(
        "app.services.profile_cache.get_profile_id_by_user_id",
        mock_get_profile_id_by_user_id,
    )
    manager = ProfileIDManager(
        db=MagicMock(),
        redis_client=redis_client,
    )
    result = await manager.get_profile_id(user_id=7)
    assert result == 1


@pytest.mark.asyncio
async def test_get_profile_id_loads_from_db_and_caches(
    redis_client,
    monkeypatch,
):
    async def mock_get_profile_id_by_user_id(user_id, db):
        assert user_id == 7
        return 1

    monkeypatch.setattr(
        "app.services.profile_cache.get_profile_id_by_user_id",
        mock_get_profile_id_by_user_id,
    )
    manager = ProfileIDManager(
        db=MagicMock(),
        redis_client=redis_client,
    )
    result = await manager.get_profile_id(user_id=7)
    assert result == 1
    assert redis_client.data["profile_service:profile_id:7"] == 1


@pytest.mark.asyncio
async def test_get_profile_id_returns_none_when_profile_not_found(
    redis_client,
    monkeypatch,
):
    async def mock_get_profile_id_by_user_id(user_id, db):
        return None

    monkeypatch.setattr(
        "app.services.profile_cache.get_profile_id_by_user_id",
        mock_get_profile_id_by_user_id,
    )

    manager = ProfileIDManager(
        db=MagicMock(),
        redis_client=redis_client,
    )
    result = await manager.get_profile_id(user_id=7)
    assert result is None
