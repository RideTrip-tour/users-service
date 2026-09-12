import base64
import json
import logging
from typing import TypedDict

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal
from app.services.devices_manager import DeviceManager
from app.services.profile_cache import ProfileIDManager
from app.utils.converters import convert_value_to_int

logger = logging.getLogger(__name__)


class DeviceInfo(TypedDict):
    device_id: str
    device_name: str | None
    platform: str | None
    user_agent: str | None


def _urlsafe_b64decode_padded(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _get_user_from_claims(claims_header: str) -> dict:
    try:
        raw = _urlsafe_b64decode_padded(claims_header)
        user = json.loads(raw.decode("utf-8"))

        if not isinstance(user, dict):
            raise TypeError("X-User-Claims must be a JSON object")
        return user
    except Exception:
        logger.warning("Invalid X-User-Claims header", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )


def _get_user_from_headers(request: Request) -> dict | None:
    claims_header = request.headers.get("x-user-claims")
    user_id_header = request.headers.get("x-user-id")

    if claims_header:
        return _get_user_from_claims(claims_header)
    if user_id_header:
        return {"id": user_id_header}
    return None


def _unauthorized_response(detail: str = "Unauthorized") -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": detail},
    )


async def _get_profile_id(
    session: AsyncSession, redis_client: Redis, user_id: int
) -> int | None:
    profile_manager = ProfileIDManager(db=session, redis_client=redis_client)
    return await profile_manager.get_profile_id(user_id=user_id)


def _get_device_from_headers(request: Request) -> DeviceInfo | None:
    device_id = request.headers.get("x-device-id")
    if device_id is not None:
        return {
            "device_id": device_id,
            "device_name": request.headers.get("x-device-name"),
            "platform": request.headers.get("sec-ch-ua-platform"),
            "user_agent": request.headers.get("user-agent"),
        }
    return None


async def _register_device(
    request: Request, session: AsyncSession, redis_client: Redis, profile_id: int
) -> None:
    device_manager = DeviceManager(db=session, redis_client=redis_client)
    device_info = _get_device_from_headers(request)
    if device_info is not None:
        await device_manager.register_device(
            profile_id=profile_id,
            **device_info,
        )


async def user_context_middleware(request: Request, call_next):
    """
    Восстанавливает request.state.user из заголовков, которые проставляет gateway.

    Ожидаемые заголовки:
    - X-User-Claims: base64url(JSON) с claims пользователя
    - X-User-ID: fallback, если нужен только идентификатор
    """
    if getattr(request.state, "user", None) is None:
        request.state.user = _get_user_from_headers(request)
        if isinstance(request.state.user, dict):
            user_id = convert_value_to_int(
                request.state.user.get("id") or request.state.user.get("sub")
            )
            if user_id is None:
                logger.warning("Unable to resolve user_id from request headers")
                return _unauthorized_response()

            async with AsyncSessionLocal() as session:
                redis_client = request.app.state.redis
                profile_id = await _get_profile_id(session, redis_client, user_id)
                if profile_id is None:
                    logger.warning("Profile not found for user_id=%s", user_id)
                    return _unauthorized_response(detail="Profile not found")
                await _register_device(request, session, redis_client, profile_id)
            request.state.user["profile_id"] = profile_id
    response = await call_next(request)
    return response
