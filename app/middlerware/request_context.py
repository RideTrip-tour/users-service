import base64
import json
import logging

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.db.database import AsyncSessionLocal
from app.services.profile_cache import ProfileIDManager
from app.utils.converters import convert_value_to_int

logger = logging.getLogger(__name__)


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


async def user_context_middleware(request: Request, call_next):
    """
    Восстанавливает request.state.user из заголовков, которые проставляет gateway.

    Ожидаемые заголовки:
    - X-User-Claims: base64url(JSON) с claims пользователя
    - X-User-ID: fallback, если нужен только идентификатор
    """
    logger.info("Middleware start")
    if getattr(request.state, "user", None) is None:
        request.state.user = _get_user_from_headers(request)
        if isinstance(request.state.user, dict):
            user_id = convert_value_to_int(
                request.state.user.get("id") or request.state.user.get("sub")
            )
            if user_id is None:
                return _unauthorized_response()

            async with AsyncSessionLocal() as session:
                profile_manager = ProfileIDManager(
                    db=session,
                    redis_client=request.app.state.redis,
                )
                profile_id = await profile_manager.get_profile_id(user_id=user_id)
            if profile_id is None:
                return _unauthorized_response(detail="Profile not found")
            request.state.user["profile_id"] = profile_id
    response = await call_next(request)
    logger.info("Middleware end")
    return response
