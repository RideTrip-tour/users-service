import logging

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.profiles_crud import get_profile_id_by_user_id
from app.utils.converters import convert_value_to_int
from config import settings

logger = logging.getLogger(__name__)


class ProfileIDManager:
    """Получает ID профиля из Redis или базы данных."""

    def __init__(self, db: AsyncSession, redis_client: Redis):
        self.db = db
        self.redis_client = redis_client

    async def get_profile_id(self, user_id: int) -> int | None:
        key = self._get_cache_key(user_id=user_id)
        cached_profile_id = await self.redis_client.get(key)
        if cached_profile_id is not None:
            logger.debug(
                "Profile ID cache hit: user_id=%s profile_id=%s",
                user_id,
                cached_profile_id,
            )
            return convert_value_to_int(cached_profile_id)
        logger.debug("Profile ID cache miss: user_id=%s", user_id)
        profile_id = await self._get_profile_id_from_db(user_id=user_id)
        logger.debug(
            "Profile ID loaded from database: user_id=%s profile_id=%s",
            user_id,
            profile_id,
        )
        await self._set_cached_profile_id(profile_id=profile_id, key=key)
        return profile_id

    async def _get_profile_id_from_db(self, user_id: int) -> int | None:
        return await get_profile_id_by_user_id(db=self.db, user_id=user_id)

    async def _set_cached_profile_id(self, profile_id: int | None, key: str) -> None:
        if profile_id is not None:
            await self.redis_client.set(
                key,
                profile_id,
                ex=settings.redis_ttl,
            )
            logger.debug("Profile ID cached: profile_id=%s", profile_id)

    @staticmethod
    def _get_cache_key(user_id: int) -> str:
        return f"profile_service:profile_id:{user_id}"
