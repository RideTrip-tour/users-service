import logging

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.devices_crud import (
    create_or_update_device as crud_create_or_update_device,
)
from app.crud.devices_crud import (
    delete_device as crud_delete_device,
)
from app.crud.devices_crud import (
    get_device as crud_get_device,
)
from app.crud.devices_crud import (
    get_devices as crud_get_devices,
)
from app.db.models import ProfileDevice
from config import settings

logger = logging.getLogger(__name__)


class DeviceManager:
    def __init__(self, db: AsyncSession, redis_client: Redis):
        self.db = db
        self.redis_client = redis_client

    async def register_device(
        self,
        profile_id: int,
        device_id: str,
        device_name: str | None = None,
        platform: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        key = self._get_cache_key(profile_id, device_id)
        cached_device_flag = await self.redis_client.get(key)
        if cached_device_flag is None:
            logger.debug(
                "Device cache miss: profile_id=%s device_id=%s",
                profile_id,
                device_id,
            )
            await crud_create_or_update_device(
                self.db,
                profile_id,
                device_id,
                device_name,
                platform,
                user_agent,
            )
            logger.info(
                "Device registered or updated: profile_id=%s device_id=%s",
                profile_id,
                device_id,
            )
            await self._set_cached_device(
                profile_id=profile_id,
                device_id=device_id,
                key=key,
            )
        logger.debug(
            "Device cache hit: profile_id=%s device_id=%s",
            profile_id,
            device_id,
        )

    async def get_device(self, profile_id: int, device_id: str) -> ProfileDevice | None:
        return await crud_get_device(self.db, profile_id, device_id)

    async def get_devices(
        self,
        profile_id: int,
    ) -> list[ProfileDevice]:
        return await crud_get_devices(self.db, profile_id)

    async def delete_device(self, profile_id: int, device_id: str) -> None:
        deleted = await crud_delete_device(self.db, profile_id, device_id)
        if deleted:
            logger.info(
                "Device deleted: profile_id=%s device_id=%s",
                profile_id,
                device_id,
            )

    @staticmethod
    def _get_cache_key(profile_id: int, device_id: str) -> str:
        return f"profile_service:device:{profile_id}:{device_id}"

    async def _set_cached_device(
        self,
        profile_id: int,
        device_id: str,
        key: str,
    ) -> None:
        await self.redis_client.set(
            key, f"{profile_id}-{device_id}", ex=settings.redis_ttl
        )
        logger.debug(
            "Device cached: profile_id=%s device_id=%s",
            profile_id,
            device_id,
        )
