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


async def list_locations(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    active_only: bool = False,
) -> list[Location]:
    """List locations in a campaign, ordered by name ascending.

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If the database query fails.
    """
    query = select(Location).where(Location.campaign_id == campaign_id).order_by(Location.name.asc())
    if active_only:
        query = query.where(Location.is_active.is_(True))
    return list(await db.scalars(query))


async def create_location(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    slug: str,
    name: str,
    description: str | None,
    is_active: bool = True,
    notes: str | None = None,
) -> Location:
    """Create a location in a campaign.

    Raises:
        LocationSlugConflictError: If the slug is already taken in this campaign.
        sqlalchemy.exc.SQLAlchemyError: If the database insert fails for other reasons.
    """
    location = Location(
        campaign_id=campaign_id,
        slug=slug,
        name=name,
        description=description,
        is_active=is_active,
        notes=notes,
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
    """Return a location by slug within a campaign, or None if not found.

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If the database query fails.
    """
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
    is_active: bool | MISSING = MISSING,
    notes: str | None | MISSING = MISSING,
) -> Location:
    """Update a campaign location's fields.

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If the database update fails.
    """
    if name is not MISSING:
        location.name = name
    if description is not MISSING:
        location.description = description
    if is_active is not MISSING:
        location.is_active = is_active
    if notes is not MISSING:
        location.notes = notes
    await db.commit()
    await db.refresh(location)
    return location


async def delete_location(db: AsyncSession, location: Location) -> None:
    """Delete a location from a campaign.

    Raises:
        sqlalchemy.exc.SQLAlchemyError: If the database delete fails.
    """
    await db.delete(location)
    await db.commit()
