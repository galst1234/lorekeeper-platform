import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pydantic.experimental.missing_sentinel import MISSING
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.database import get_db
from api.models import CampaignMember, Location, MemberRole
from api.routers._openapi import CONFLICT, FORBIDDEN, INVALID_IMAGE, NOT_FOUND, UNAUTHENTICATED, UNPROCESSABLE
from api.routers._slugs import NonReservedSlugModel
from api.routers._tags import normalize_tags_or_422
from api.routers.campaigns.dependencies import require_campaign_member
from api.services import locations as location_service
from api.services.locations import LocationSlugConflictError
from api.storage import ALLOWED_IMAGE_CONTENT_TYPES, ImageStorage, get_image_storage

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
                "restricted": False,
                "tags": ["tavern", "safe-haven"],
                "image_url": "/media/6b1f0c2d-2c8f-4d3a-8a1e-1a2b3c4d5e6f.png",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z",
            }
        }
    )

    id: uuid.UUID
    slug: str
    name: str
    description: str | None
    restricted: bool
    tags: list[str]
    image_url: str | None
    created_at: datetime
    updated_at: datetime


class CreateLocationRequest(NonReservedSlugModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "slug": "moonlit-tavern",
                "name": "Moonlit Tavern",
                "description": "A cozy inn on the edge of the Whisperwood.",
                "tags": ["tavern", "safe-haven"],
            }
        }
    )

    name: _NonEmptyStr
    description: str | None = None
    restricted: bool = False
    tags: list[str] = Field(default_factory=list)


class PatchLocationRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Moonlit Tavern, Rebuilt",
                "description": "Rebuilt after the fire.",
                "tags": ["tavern", "safe-haven"],
            }
        }
    )

    name: _NonEmptyStr | MISSING = MISSING
    description: str | None | MISSING = MISSING
    restricted: bool | MISSING = MISSING
    tags: list[str] | MISSING = MISSING


def _to_response(location: Location, image_storage: ImageStorage) -> LocationResponse:
    return LocationResponse(
        id=location.id,
        slug=location.slug,
        name=location.name,
        description=location.description,
        restricted=location.restricted,
        tags=location.tags,
        image_url=image_storage.url_for(location.image_key) if location.image_key else None,
        created_at=location.created_at,
        updated_at=location.updated_at,
    )


@router.get("", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def list_locations(
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> list[LocationResponse]:
    locations = await location_service.list_locations(db, member.campaign_id, member.role)
    return [_to_response(location, image_storage) for location in locations]


@router.post("", status_code=201, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND | CONFLICT | UNPROCESSABLE)
async def create_location(
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    body: CreateLocationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> LocationResponse:
    if body.restricted and member.role != MemberRole.GM:
        raise HTTPException(status_code=403, detail="Only the GM can create a restricted location")
    normalized_tags = normalize_tags_or_422(body.tags)
    try:
        location = await location_service.create_location(
            db,
            campaign_id=member.campaign_id,
            slug=body.slug,
            name=body.name,
            description=body.description,
            restricted=body.restricted,
            tags=normalized_tags,
        )
    except LocationSlugConflictError:
        raise HTTPException(
            status_code=409,
            detail="A location with that slug already exists in this campaign",
        ) from None
    return _to_response(location, image_storage)


@router.get("/{location_slug}", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def get_location(
    location_slug: str,
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> LocationResponse:
    location = await location_service.get_location_by_slug(db, member.campaign_id, location_slug, member.role)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    return _to_response(location, image_storage)


@router.patch("/{location_slug}", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND | UNPROCESSABLE)
async def patch_location(
    location_slug: str,
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    body: PatchLocationRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> LocationResponse:
    if body.restricted is not MISSING and body.restricted and member.role != MemberRole.GM:
        raise HTTPException(status_code=403, detail="Only the GM can mark a location as restricted")
    if body.tags is MISSING:
        tags_update: list[str] | MISSING = MISSING
    else:
        tags_update = normalize_tags_or_422(body.tags)
    location = await location_service.get_location_by_slug(db, member.campaign_id, location_slug, member.role)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    updated = await location_service.update_location(
        db,
        location,
        name=body.name,
        description=body.description,
        restricted=body.restricted,
        tags=tags_update,
    )
    return _to_response(updated, image_storage)


@router.delete("/{location_slug}", status_code=204, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def delete_location(
    location_slug: str,
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> None:
    location = await location_service.get_location_by_slug(db, member.campaign_id, location_slug, member.role)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    await location_service.delete_location(db, location, image_storage)


@router.put("/{location_slug}/image", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND | INVALID_IMAGE)
async def upload_location_image(
    location_slug: str,
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
    file: Annotated[UploadFile, File()],
) -> LocationResponse:
    location = await location_service.get_location_by_slug(db, member.campaign_id, location_slug, member.role)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported image type")
    content = await file.read(settings.image_max_size_bytes + 1)
    if len(content) > settings.image_max_size_bytes:
        raise HTTPException(status_code=400, detail="Image exceeds maximum size")
    new_key = await image_storage.save(content, file.content_type)
    try:
        updated = await location_service.set_location_image(db, location, new_key, image_storage)
    except Exception:
        await image_storage.delete(new_key)
        raise
    return _to_response(updated, image_storage)


@router.delete("/{location_slug}/image", status_code=204, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def delete_location_image(
    location_slug: str,
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> None:
    location = await location_service.get_location_by_slug(db, member.campaign_id, location_slug, member.role)
    if location is None:
        raise HTTPException(status_code=404, detail="Location not found")
    await location_service.clear_location_image(db, location, image_storage)
