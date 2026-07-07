import uuid
from dataclasses import dataclass
from datetime import datetime

from asyncpg import UniqueViolationError
from pydantic_core import MISSING
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import CampaignLocation, Location


class LocationSlugConflictError(Exception):
    pass


class LocationAlreadyLinkedError(Exception):
    pass


@dataclass(frozen=True)
class LinkedLocation:
    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    is_active: bool
    notes: str | None
    added_at: datetime
    created_at: datetime
    updated_at: datetime


def _is_slug_conflict(exc: BaseException) -> bool:
    if not isinstance(exc, IntegrityError) or exc.orig is None:
        return False
    original_error = exc.orig.__cause__
    return (
        isinstance(original_error, UniqueViolationError)
        and getattr(original_error, "constraint_name", None) == Location.SLUG_UNIQUE_CONSTRAINT
    )


def _to_linked_location(location: Location, campaign_location: CampaignLocation) -> LinkedLocation:
    return LinkedLocation(
        id=location.id,
        slug=location.slug,
        name=location.name,
        description=location.description,
        is_active=campaign_location.is_active,
        notes=campaign_location.notes,
        added_at=campaign_location.added_at,
        created_at=location.created_at,
        updated_at=location.updated_at,
    )


async def create_and_link(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    owner_id: uuid.UUID,
    slug: str,
    name: str,
    description: str | None = None,
    notes: str | None = None,
    is_active: bool = True,
) -> LinkedLocation:
    """Create a canonical location and link it to a campaign.

    Raises:
        LocationSlugConflictError: If the slug is already taken for this owner.
    """
    location = Location(
        owner_id=owner_id,
        slug=slug,
        name=name,
        description=description,
    )
    try:
        db.add(location)
        await db.flush()
        campaign_location = CampaignLocation(
            campaign_id=campaign_id,
            location_id=location.id,
            is_active=is_active,
            notes=notes,
        )
        db.add(campaign_location)
        await db.flush()
        await db.commit()
        await db.refresh(location)
        await db.refresh(campaign_location)
        return _to_linked_location(location, campaign_location)
    except IntegrityError as exc:
        await db.rollback()
        if _is_slug_conflict(exc):
            raise LocationSlugConflictError() from exc
        raise


async def link_location(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    location_id: uuid.UUID,
) -> LinkedLocation:
    """Link an existing canonical location to a campaign.

    Raises:
        LocationAlreadyLinkedError: If the location is already linked to this campaign.
    """
    existing = await db.scalar(
        select(CampaignLocation).where(
            CampaignLocation.campaign_id == campaign_id,
            CampaignLocation.location_id == location_id,
        )
    )
    if existing is not None:
        raise LocationAlreadyLinkedError()

    campaign_location = CampaignLocation(
        campaign_id=campaign_id,
        location_id=location_id,
    )
    db.add(campaign_location)
    await db.flush()
    await db.commit()
    await db.refresh(campaign_location)
    location = await db.get(Location, location_id)
    if location is None:
        raise ValueError(f"Location {location_id} not found")
    return _to_linked_location(location, campaign_location)


async def unlink_campaign_location(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    location_slug: str,
) -> None:
    """Remove a campaign-location link without deleting the canonical location."""
    campaign_location = await db.scalar(
        select(CampaignLocation)
        .join(Location, CampaignLocation.location_id == Location.id)
        .where(
            CampaignLocation.campaign_id == campaign_id,
            Location.slug == location_slug,
        )
    )
    if campaign_location is None:
        return
    await db.delete(campaign_location)
    await db.commit()


async def update_campaign_location(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    location_slug: str,
    *,
    is_active: bool | MISSING = MISSING,
    notes: str | None | MISSING = MISSING,
) -> LinkedLocation:
    """Update junction fields for a linked campaign location."""
    row = await db.execute(
        select(Location, CampaignLocation)
        .join(CampaignLocation, CampaignLocation.location_id == Location.id)
        .where(
            CampaignLocation.campaign_id == campaign_id,
            Location.slug == location_slug,
        )
    )
    result = row.one()
    location, campaign_location = result
    if is_active is not MISSING:
        campaign_location.is_active = is_active
    if notes is not MISSING:
        campaign_location.notes = notes
    await db.commit()
    await db.refresh(location)
    await db.refresh(campaign_location)
    return _to_linked_location(location, campaign_location)


async def list_campaign_locations(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    active_only: bool = False,
) -> list[LinkedLocation]:
    """List locations linked to a campaign, ordered by name ascending."""
    query = (
        select(Location, CampaignLocation)
        .join(CampaignLocation, CampaignLocation.location_id == Location.id)
        .where(CampaignLocation.campaign_id == campaign_id)
        .order_by(Location.name.asc())
    )
    if active_only:
        query = query.where(CampaignLocation.is_active.is_(True))
    rows = await db.execute(query)
    return [_to_linked_location(location, campaign_location) for location, campaign_location in rows.all()]


async def get_linked_location_by_slug(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    location_slug: str,
) -> LinkedLocation | None:
    """Return a linked location by slug, or None if not linked to this campaign."""
    row = await db.execute(
        select(Location, CampaignLocation)
        .join(CampaignLocation, CampaignLocation.location_id == Location.id)
        .where(
            CampaignLocation.campaign_id == campaign_id,
            Location.slug == location_slug,
        )
    )
    result = row.one_or_none()
    if result is None:
        return None
    location, campaign_location = result
    return _to_linked_location(location, campaign_location)
