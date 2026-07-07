import uuid

from asyncpg import UniqueViolationError
from pydantic_core import MISSING
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Location


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


async def list_locations(db: AsyncSession, campaign_id: uuid.UUID) -> list[Location]:
    query = select(Location).where(Location.campaign_id == campaign_id).order_by(Location.name.asc())
    return list(await db.scalars(query))


async def create_location(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    slug: str,
    name: str,
    description: str | None,
) -> Location:
    location = Location(
        campaign_id=campaign_id,
        slug=slug,
        name=name,
        description=description,
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
) -> Location | None:
    return await db.scalar(
        select(Location).where(
            Location.campaign_id == campaign_id,
            Location.slug == location_slug,
        )
    )


async def update_location(
    db: AsyncSession,
    location: Location,
    *,
    name: str | MISSING = MISSING,
    description: str | None | MISSING = MISSING,
) -> Location:
    if name is not MISSING:
        location.name = name
    if description is not MISSING:
        location.description = description
    await db.commit()
    await db.refresh(location)
    return location


async def delete_location(db: AsyncSession, location: Location) -> None:
    await db.delete(location)
    await db.commit()
