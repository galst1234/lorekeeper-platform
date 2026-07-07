import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, StringConstraints
from pydantic.experimental.missing_sentinel import MISSING
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import Campaign, Location
from api.routers._openapi import CONFLICT, FORBIDDEN, NOT_FOUND, UNAUTHENTICATED
from api.routers._slugs import NonReservedSlugModel
from api.routers.campaigns.dependencies import require_campaign_member
from api.services import locations as location_service
from api.services.locations import LocationSlugConflictError

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
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z",
            }
        }
    )

    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class CreateLocationRequest(NonReservedSlugModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "slug": "moonlit-tavern",
                "name": "Moonlit Tavern",
                "description": "A cozy inn on the edge of the Whisperwood.",
            }
        }
    )

    name: _NonEmptyStr
    description: str | None = None


class PatchLocationRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Moonlit Tavern, Rebuilt",
                "description": "Rebuilt after the fire.",
            }
        }
    )

    name: _NonEmptyStr | MISSING = MISSING
    description: str | None | MISSING = MISSING


def _to_response(location: Location) -> LocationResponse:
    return LocationResponse(
        id=location.id,
        slug=location.slug,
        name=location.name,
        description=location.description,
        created_at=location.created_at,
        updated_at=location.updated_at,
    )


@router.get("", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def list_locations(
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[LocationResponse]:
    locations = await location_service.list_locations(db, campaign.id)
    return [_to_response(location) for location in locations]


@router.post("", status_code=201, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND | CONFLICT)
async def create_location(
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    body: CreateLocationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LocationResponse:
    try:
        location = await location_service.create_location(
            db,
            campaign_id=campaign.id,
            slug=body.slug,
            name=body.name,
            description=body.description,
        )
    except LocationSlugConflictError:
        raise HTTPException(
            status_code=409,
            detail="A location with that slug already exists in this campaign",
        ) from None
    return _to_response(location)


@router.get("/{location_slug}", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def get_location(
    location_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LocationResponse:
    location = await location_service.get_location_by_slug(db, campaign.id, location_slug)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return _to_response(location)


@router.patch("/{location_slug}", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def patch_location(
    location_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    body: PatchLocationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LocationResponse:
    location = await location_service.get_location_by_slug(db, campaign.id, location_slug)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    updated = await location_service.update_location(
        db,
        location,
        name=body.name,
        description=body.description,
    )
    return _to_response(updated)


@router.delete("/{location_slug}", status_code=204, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def delete_location(
    location_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    location = await location_service.get_location_by_slug(db, campaign.id, location_slug)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    await location_service.delete_location(db, location)
