from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ProfileDevice


async def _find_by_id(
    db: AsyncSession, profile_id: int, device_id: str
) -> ProfileDevice | None:
    result = await db.execute(
        select(ProfileDevice).where(
            ProfileDevice.profile_id == profile_id,
            ProfileDevice.device_id == device_id,
        )
    )
    return result.scalar_one_or_none()


async def _find_devices(db: AsyncSession, profile_id: int) -> list[ProfileDevice]:
    result = await db.execute(
        select(ProfileDevice)
        .where(ProfileDevice.profile_id == profile_id)
        .order_by(ProfileDevice.last_seen_at.desc())
    )
    return list(result.scalars().all())


async def _create_device(
    db: AsyncSession,
    device: ProfileDevice,
) -> ProfileDevice:
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return device


async def _update_last_seen(db: AsyncSession, device: ProfileDevice) -> ProfileDevice:
    device.last_seen_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(device)
    return device


async def _delete_device(db: AsyncSession, device: ProfileDevice | None) -> bool:
    if device is None:
        return False
    await db.delete(device)
    await db.commit()
    return True


async def get_device(
    db: AsyncSession,
    profile_id: int,
    device_id: str,
) -> ProfileDevice | None:
    return await _find_by_id(db=db, profile_id=profile_id, device_id=device_id)


async def create_or_update_device(
    db: AsyncSession,
    profile_id: int,
    device_id: str,
    device_name: str | None = None,
    platform: str | None = None,
    user_agent: str | None = None,
) -> ProfileDevice:
    device = await _find_by_id(db=db, profile_id=profile_id, device_id=device_id)

    if device is None:
        device = ProfileDevice(
            profile_id=profile_id,
            device_id=device_id,
            device_name=device_name,
            platform=platform,
            user_agent=user_agent,
        )
        return await _create_device(db, device)

    return await _update_last_seen(
        db=db,
        device=device,
    )


async def get_devices(db: AsyncSession, profile_id: int) -> list[ProfileDevice]:
    return await _find_devices(db, profile_id)


async def delete_device(db: AsyncSession, profile_id: int, device_id: str) -> bool:
    device = await _find_by_id(db=db, profile_id=profile_id, device_id=device_id)
    return await _delete_device(db=db, device=device)
