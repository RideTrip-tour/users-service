import os
import sys
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ["DEBUG"] = "false"

from app.dependencies.profiles import get_profile_manager
from app.services.devices_manager import DeviceManager
from app.services.profile_cache import ProfileIDManager
from main import create_app

INVALID_PROFILE_FIELDS = [
    ("about_me", "A" * 201),
    ("activities", ["A"] * 26),
    ("country", "A"),
    ("country", "A" * 26),
    ("city", "A"),
    ("city", "A" * 26),
    ("citizenship", "A"),
    ("citizenship", "A" * 16),
    ("currency", "RU"),
    ("currency", "RUBB"),
    ("birth_date", "2002.09.09"),
]


class StubRedis:
    pass


@pytest.fixture
def app():
    app = create_app()
    app.state.redis = StubRedis()
    return app


@pytest_asyncio.fixture
async def client(app) -> Generator[AsyncClient, None, None]:

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as test_client:
        yield test_client


@pytest.fixture
def override_manager(app):
    def _override(manager):
        async def _get_manager():
            return manager

        app.dependency_overrides[get_profile_manager] = _get_manager
        return manager

    yield _override
    app.dependency_overrides.clear()


class MockRedis:
    def __init__(self):
        self.data = {}

    async def get(self, key):
        return self.data.get(key)

    async def set(self, key, value, ex=None):
        self.data[key] = value

    async def delete(self, key):
        self.data.pop(key, None)


@pytest.fixture
def redis_client():
    return MockRedis()


@pytest.fixture
def today():
    return datetime.now(UTC).date()


@pytest.fixture
def device_manager(redis_client):
    return DeviceManager(
        db=MagicMock(),
        redis_client=redis_client,
    )


@pytest.fixture
def profile_id_manager(redis_client):
    return ProfileIDManager(
        db=MagicMock(),
        redis_client=redis_client,
    )
