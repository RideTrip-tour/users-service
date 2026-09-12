from unittest.mock import MagicMock

import pytest

from app.db.models import ProfileDevice


@pytest.mark.asyncio
async def test_register_device_returns_without_database_call_when_cached(
    device_manager,
    redis_client,
    monkeypatch,
):
    redis_client.data["profile_service:device:7:device-7"] = "7-device-7"

    async def mock_create_or_update_device(*args, **kwargs):
        pytest.fail("Database should not be called")

    monkeypatch.setattr(
        "app.services.devices_manager.crud_create_or_update_device",
        mock_create_or_update_device,
    )
    result = await device_manager.register_device(
        profile_id=7,
        device_id="device-7",
    )
    assert result is None


@pytest.mark.asyncio
async def test_register_device_creates_or_updates_device_when_not_cached(
    device_manager,
    redis_client,
    monkeypatch,
):
    async def mock_create_or_update_device(
        db,
        profile_id,
        device_id,
        device_name,
        platform,
        user_agent,
    ):
        assert db is device_manager.db
        assert profile_id == 7
        assert device_id == "device-7"
        assert device_name == "Chrome"
        assert platform == '"Windows"'
        assert user_agent == "Mozilla/5.0"

    monkeypatch.setattr(
        "app.services.devices_manager.crud_create_or_update_device",
        mock_create_or_update_device,
    )
    result = await device_manager.register_device(
        profile_id=7,
        device_id="device-7",
        device_name="Chrome",
        platform='"Windows"',
        user_agent="Mozilla/5.0",
    )
    assert result is None
    assert redis_client.data["profile_service:device:7:device-7"] == "7-device-7"


@pytest.mark.asyncio
async def test_register_device_uses_correct_cache_key(
    device_manager,
    redis_client,
    monkeypatch,
):
    async def mock_create_or_update_device(*args, **kwargs):
        pass

    monkeypatch.setattr(
        "app.services.devices_manager.crud_create_or_update_device",
        mock_create_or_update_device,
    )
    await device_manager.register_device(
        profile_id=10,
        device_id="device-10",
    )
    assert "profile_service:device:10:device-10" in redis_client.data


@pytest.mark.asyncio
async def test_get_device(device_manager, monkeypatch):
    device = MagicMock(spec=ProfileDevice)

    async def mock_get_device(db, profile_id, device_id):
        assert db is device_manager.db
        assert profile_id == 7
        assert device_id == "device-7"
        return device

    monkeypatch.setattr(
        "app.services.devices_manager.crud_get_device",
        mock_get_device,
    )
    result = await device_manager.get_device(
        profile_id=7,
        device_id="device-7",
    )
    assert result is device


@pytest.mark.asyncio
async def test_get_device_returns_none_when_device_not_found(
    device_manager, monkeypatch
):
    async def mock_get_device(db, profile_id, device_id):
        return None

    monkeypatch.setattr(
        "app.services.devices_manager.crud_get_device",
        mock_get_device,
    )
    result = await device_manager.get_device(
        profile_id=7,
        device_id="device-7",
    )
    assert result is None


@pytest.mark.asyncio
async def test_get_devices(device_manager, monkeypatch):
    devices = [
        MagicMock(spec=ProfileDevice),
        MagicMock(spec=ProfileDevice),
    ]

    async def mock_get_devices(db, profile_id):
        assert db is device_manager.db
        assert profile_id == 7
        return devices

    monkeypatch.setattr(
        "app.services.devices_manager.crud_get_devices",
        mock_get_devices,
    )
    result = await device_manager.get_devices(profile_id=7)
    assert result == devices


@pytest.mark.asyncio
async def test_get_devices_returns_empty_list(device_manager, monkeypatch):
    async def mock_get_devices(db, profile_id):
        return []

    monkeypatch.setattr(
        "app.services.devices_manager.crud_get_devices",
        mock_get_devices,
    )
    result = await device_manager.get_devices(profile_id=7)
    assert result == []


@pytest.mark.asyncio
async def test_delete_device(device_manager, monkeypatch):
    async def mock_delete_device(db, profile_id, device_id):
        assert db is device_manager.db
        assert profile_id == 7
        assert device_id == "device-7"
        return True

    monkeypatch.setattr(
        "app.services.devices_manager.crud_delete_device",
        mock_delete_device,
    )

    result = await device_manager.delete_device(
        profile_id=7,
        device_id="device-7",
    )
    assert result is None


@pytest.mark.asyncio
async def test_delete_device_when_device_not_found(device_manager, monkeypatch):
    async def mock_delete_device(db, profile_id, device_id):
        return False

    monkeypatch.setattr(
        "app.services.devices_manager.crud_delete_device",
        mock_delete_device,
    )
    result = await device_manager.delete_device(
        profile_id=7,
        device_id="device-7",
    )
    assert result is None
