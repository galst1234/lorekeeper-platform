import logging
import uuid

from asyncpg import UniqueViolationError
from pydantic_core import MISSING
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Location, MemberRole
from api.services.common.visibility import apply_visibility_filter
from api.storage import ImageStorage

logger = logging.getLogger(__name__)


class LocationSlugConflictError(Exception):
    pass


def _is_slug_conflict(exc: BaseException) -> bool:
    if not isinstance(exc, IntegrityError) or exc.orig is None:
        return False
    original_error = exc.orig.__cause__
    return (
        isinstance(original_error, UniqueViolationError)
        and getattr(original_error, "constraint_name", None) == Location.SLUG_UNIQUE_CONSTRAINT
    )


async def list_locations(db: AsyncSession, campaign_id: uuid.UUID, requester_role: MemberRole) -> list[Location]:
    query = select(Location).where(Location.campaign_id == campaign_id).order_by(Location.name.asc())
    query = apply_visibility_filter(query, Location, requester_role)
    return list(await db.scalars(query))


async def create_location(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    slug: str,
    name: str,
    description: str | None,
    restricted: bool = False,
    tags: list[str] | None = None,
) -> Location:
    location = Location(
        campaign_id=campaign_id,
        slug=slug,
        name=name,
        description=description,
        restricted=restricted,
        tags=tags if tags is not None else [],
    )
    try:
        db.add(location)
        await db.flush()
        await db.commit()
        await db.refresh(location)
        return location
    except IntegrityError as exc:
        await db.rollback()
        if _is_slug_conflict(exc):
            raise LocationSlugConflictError() from exc
        raise


async def get_location_by_slug(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    location_slug: str,
    requester_role: MemberRole,
    *,
    for_update: bool = False,
) -> Location | None:
    query = select(Location).where(
        Location.campaign_id == campaign_id,
        Location.slug == location_slug,
    )
    query = apply_visibility_filter(query, Location, requester_role)
    if for_update:
        query = query.with_for_update()
    return await db.scalar(query)


async def update_location(
    db: AsyncSession,
    location: Location,
    *,
    name: str | MISSING = MISSING,
    description: str | None | MISSING = MISSING,
    restricted: bool | MISSING = MISSING,
    tags: list[str] | MISSING = MISSING,
) -> Location:
    if name is not MISSING:
        location.name = name
    if description is not MISSING:
        location.description = description
    if restricted is not MISSING:
        location.restricted = restricted
    if tags is not MISSING:
        location.tags = tags
    await db.commit()
    await db.refresh(location)
    return location


async def delete_location(db: AsyncSession, location: Location, image_storage: ImageStorage) -> None:
    image_key = location.image_key
    await db.delete(location)
    await db.commit()
    if image_key is not None:
        try:
            await image_storage.delete(image_key)
        except Exception:
            logger.warning("Failed to delete image %s for deleted location %s", image_key, location.id)


async def list_location_image_keys(db: AsyncSession, campaign_id: uuid.UUID) -> list[str]:
    return [
        key
        for key in await db.scalars(
            select(Location.image_key).where(Location.campaign_id == campaign_id, Location.image_key.is_not(None))
        )
        if key is not None
    ]


async def set_location_image(
    db: AsyncSession,
    location: Location,
    new_image_key: str,
    image_storage: ImageStorage,
) -> Location:
    old_key = location.image_key
    location.image_key = new_image_key
    await db.commit()
    try:
        await db.refresh(location)
    except Exception:
        logger.warning("Failed to refresh location %s after image update", location.id)
    if old_key is not None:
        try:
            await image_storage.delete(old_key)
        except Exception:
            logger.warning("Failed to delete old image %s for location %s", old_key, location.id)
    return location


async def clear_location_image(db: AsyncSession, location: Location, image_storage: ImageStorage) -> Location:
    old_key = location.image_key
    location.image_key = None
    await db.commit()
    try:
        await db.refresh(location)
    except Exception:
        logger.warning("Failed to refresh location %s after image update", location.id)
    if old_key is not None:
        try:
            await image_storage.delete(old_key)
        except Exception:
            logger.warning("Failed to delete old image %s for location %s", old_key, location.id)
    return location
