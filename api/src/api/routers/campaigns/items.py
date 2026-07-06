import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, StringConstraints
from pydantic.experimental.missing_sentinel import MISSING
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import Campaign, Item
from api.routers._openapi import CONFLICT, FORBIDDEN, NOT_FOUND, UNAUTHENTICATED
from api.routers._slugs import NonReservedSlugModel
from api.routers.campaigns.dependencies import require_campaign_member
from api.services import items as item_service
from api.services.items import ItemSlugConflictError

router = APIRouter(prefix="/items", tags=["Items"])

_NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ItemResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "a4c2b1d0-e3f5-4789-abcd-ef0123456789",
                "slug": "moonblade",
                "name": "Moonblade",
                "description": "A blade that glows under moonlight.",
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


class CreateItemRequest(NonReservedSlugModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "slug": "moonblade",
                "name": "Moonblade",
                "description": "A blade that glows under moonlight.",
            }
        }
    )

    name: _NonEmptyStr
    description: str | None = None


class PatchItemRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Moonblade, Reforged",
                "description": "Updated description.",
            }
        }
    )

    name: _NonEmptyStr | MISSING = MISSING
    description: str | None | MISSING = MISSING


def _to_response(item: Item) -> ItemResponse:
    return ItemResponse(
        id=item.id,
        slug=item.slug,
        name=item.name,
        description=item.description,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def list_items(
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ItemResponse]:
    items = await item_service.list_items(db, campaign.id)
    return [_to_response(item) for item in items]


@router.post("", status_code=201, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND | CONFLICT)
async def create_item(
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    body: CreateItemRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
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
    return _to_response(item)


@router.get("/{item_slug}", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def get_item(
    item_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ItemResponse:
    item = await item_service.get_item_by_slug(db, campaign.id, item_slug)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return _to_response(item)


@router.patch("/{item_slug}", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def patch_item(
    item_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    body: PatchItemRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ItemResponse:
    item = await item_service.get_item_by_slug(db, campaign.id, item_slug)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    updated = await item_service.update_item(
        db,
        item,
        name=body.name,
        description=body.description,
    )
    return _to_response(updated)


@router.delete("/{item_slug}", status_code=204, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def delete_item(
    item_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    item = await item_service.get_item_by_slug(db, campaign.id, item_slug)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    await item_service.delete_item(db, item)
