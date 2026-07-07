import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, StringConstraints
from pydantic.experimental.missing_sentinel import MISSING
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models import Campaign, User
from api.routers._openapi import CONFLICT, FORBIDDEN, NOT_FOUND, UNAUTHENTICATED
from api.routers._slugs import NonReservedSlugModel
from api.routers.campaigns.dependencies import require_campaign_member
from api.services import campaign_locations as location_service
from api.services.campaign_locations import (
    LinkedLocation,
    LocationAlreadyLinkedError,
    LocationSlugConflictError,
)

router = APIRouter(prefix="/locations", tags=["Locations"])

_NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class LocationResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "a4c2b1d0-e3f5-4789-abcd-ef0123456789",
                "slug": "moonlit-tavern",
                "name": "Moonlit Tavern",
                "description": "A cozy inn on the edge of the Whisperwood.",
                "is_active": True,
                "notes": "Party rested here after Session 3.",
                "added_at": "2024-01-15T10:00:00Z",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z",
            }
        }
    )

    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    is_active: bool
    notes: str | None
    added_at: datetime
    created_at: datetime
    updated_at: datetime


class CreateLocationRequest(NonReservedSlugModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "slug": "moonlit-tavern",
                "name": "Moonlit Tavern",
                "description": "A cozy inn on the edge of the Whisperwood.",
                "notes": "Party rested here after Session 3.",
                "is_active": True,
            }
        }
    )

    name: _NonEmptyStr
    description: str | None = None
    notes: str | None = None
    is_active: bool = True


class PatchLocationRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_active": False,
                "notes": "Abandoned after the dragon attack.",
            }
        }
    )

    is_active: bool | MISSING = MISSING
    notes: str | None | MISSING = MISSING


def _to_response(linked: LinkedLocation) -> LocationResponse:
    return LocationResponse(
        id=linked.id,
        slug=linked.slug,
        name=linked.name,
        description=linked.description,
        is_active=linked.is_active,
        notes=linked.notes,
        added_at=linked.added_at,
        created_at=linked.created_at,
        updated_at=linked.updated_at,
    )


@router.get("", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def list_campaign_locations(
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    active_only: bool = False,
) -> list[LocationResponse]:
    locations = await location_service.list_campaign_locations(db, campaign.id, active_only=active_only)
    return [_to_response(location) for location in locations]


@router.post("", status_code=201, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND | CONFLICT)
async def create_campaign_location(
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    body: CreateLocationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> LocationResponse:
    try:
        linked = await location_service.create_and_link(
            db,
            campaign_id=campaign.id,
            owner_id=user.id,
            slug=body.slug,
            name=body.name,
            description=body.description,
            notes=body.notes,
            is_active=body.is_active,
        )
    except LocationSlugConflictError:
        raise HTTPException(status_code=409, detail="A location with that slug already exists") from None
    except LocationAlreadyLinkedError:
        raise HTTPException(
            status_code=409,
            detail="This location is already linked to the campaign",
        ) from None
    return _to_response(linked)


@router.get("/{location_slug}", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def get_campaign_location(
    location_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LocationResponse:
    linked = await location_service.get_linked_location_by_slug(db, campaign.id, location_slug)
    if linked is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return _to_response(linked)


@router.patch("/{location_slug}", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def patch_campaign_location(
    location_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    body: PatchLocationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LocationResponse:
    linked = await location_service.get_linked_location_by_slug(db, campaign.id, location_slug)
    if linked is None:
        raise HTTPException(status_code=404, detail="Location not found")
    updated = await location_service.update_campaign_location(
        db,
        campaign.id,
        location_slug,
        is_active=body.is_active,
        notes=body.notes,
    )
    return _to_response(updated)


@router.delete("/{location_slug}", status_code=204, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def unlink_campaign_location(
    location_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    linked = await location_service.get_linked_location_by_slug(db, campaign.id, location_slug)
    if linked is None:
        raise HTTPException(status_code=404, detail="Location not found")
    await location_service.unlink_campaign_location(db, campaign.id, location_slug)
