import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, StringConstraints
from pydantic.experimental.missing_sentinel import MISSING
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.database import get_db
from api.models import Campaign, Item
from api.routers._openapi import CONFLICT, FORBIDDEN, INVALID_IMAGE, NOT_FOUND, UNAUTHENTICATED
from api.routers._slugs import NonReservedSlugModel
from api.routers.campaigns.dependencies import require_campaign_member
from api.services import items as item_service
from api.services.items import ItemSlugConflictError
from api.storage import ALLOWED_IMAGE_CONTENT_TYPES, ImageStorage, get_image_storage

router = APIRouter(prefix="/items", tags=["Items"])

_NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ItemResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "b5d3c2e1-f406-489a-bcde-f01234567890",
                "slug": "sunblade",
                "name": "Sunblade",
                "description": "A radiant longsword that glows in the presence of undead.",
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
    image_url: str | None
    created_at: datetime
    updated_at: datetime


class CreateItemRequest(NonReservedSlugModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "slug": "sunblade",
                "name": "Sunblade",
                "description": "A radiant longsword that glows in the presence of undead.",
            }
        }
    )

    name: _NonEmptyStr
    description: str | None = None


class PatchItemRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Sunblade, Reforged",
                "description": "Updated description.",
            }
        }
    )

    name: _NonEmptyStr | MISSING = MISSING
    description: str | None | MISSING = MISSING


def _to_response(item: Item, image_storage: ImageStorage) -> ItemResponse:
    return ItemResponse(
        id=item.id,
        slug=item.slug,
        name=item.name,
        description=item.description,
        image_url=image_storage.url_for(item.image_key) if item.image_key else None,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def list_items(
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> list[ItemResponse]:
    items = await item_service.list_items(db, campaign.id)
    return [_to_response(item, image_storage) for item in items]


@router.post("", status_code=201, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND | CONFLICT)
async def create_item(
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    body: CreateItemRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> ItemResponse:
    try:
        item = await item_service.create_item(
            db,
            campaign_id=campaign.id,
            slug=body.slug,
            name=body.name,
            description=body.description,
        )
    except ItemSlugConflictError:
        raise HTTPException(status_code=409, detail="An item with that slug already exists in this campaign") from None
    return _to_response(item, image_storage)


@router.get("/{item_slug}", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def get_item(
    item_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> ItemResponse:
    item = await item_service.get_item_by_slug(db, campaign.id, item_slug)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return _to_response(item, image_storage)


@router.patch("/{item_slug}", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def patch_item(
    item_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    body: PatchItemRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> ItemResponse:
    item = await item_service.get_item_by_slug(db, campaign.id, item_slug)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    updated = await item_service.update_item(db, item, name=body.name, description=body.description)
    return _to_response(updated, image_storage)


@router.delete("/{item_slug}", status_code=204, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def delete_item(
    item_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> None:
    item = await item_service.get_item_by_slug(db, campaign.id, item_slug)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    await item_service.delete_item(db, item, image_storage)


@router.put("/{item_slug}/image", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND | INVALID_IMAGE)
async def upload_item_image(
    item_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
    file: Annotated[UploadFile, File()],
) -> ItemResponse:
    item = await item_service.get_item_by_slug(db, campaign.id, item_slug)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported image type")
    content = await file.read(settings.image_max_size_bytes + 1)
    if len(content) > settings.image_max_size_bytes:
        raise HTTPException(status_code=400, detail="Image exceeds maximum size")
    new_key = await image_storage.save(content, file.content_type)
    try:
        updated = await item_service.set_item_image(db, item, new_key, image_storage)
    except Exception:
        await image_storage.delete(new_key)
        raise
    return _to_response(updated, image_storage)


@router.delete("/{item_slug}/image", status_code=204, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def delete_item_image(
    item_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> None:
    item = await item_service.get_item_by_slug(db, campaign.id, item_slug)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    await item_service.clear_item_image(db, item, image_storage)
