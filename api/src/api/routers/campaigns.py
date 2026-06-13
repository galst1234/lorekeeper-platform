import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, StringConstraints
from pydantic.experimental.missing_sentinel import MISSING
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models.campaign import Campaign
from api.models.user import User
from api.services import campaigns as campaign_service

router = APIRouter()

_NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
_SlugLabelStr = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$",
    ),
]


class CampaignResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    slug: str
    created_at: datetime
    updated_at: datetime


class CreateCampaignRequest(BaseModel):
    name: _NonEmptyStr
    description: str | None = None
    slug_label: _SlugLabelStr


class PatchCampaignRequest(BaseModel):
    name: _NonEmptyStr | MISSING = MISSING
    description: str | None | MISSING = MISSING
    slug_label: _SlugLabelStr | MISSING = MISSING


def _to_response(campaign: Campaign) -> CampaignResponse:
    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        slug=campaign.slug,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


@router.get("/campaigns")
async def list_campaigns(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CampaignResponse]:
    campaigns = await campaign_service.list_campaigns(db, user.id)
    return [_to_response(campaign) for campaign in campaigns]


@router.post("/campaigns", status_code=201)
async def create_campaign(
    body: CreateCampaignRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CampaignResponse:
    campaign = await campaign_service.create_campaign(
        db,
        owner_id=user.id,
        name=body.name,
        description=body.description,
        slug_label=body.slug_label,
    )

    return _to_response(campaign)


@router.get("/campaigns/{slug}", response_model=None)
async def get_campaign(
    slug: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CampaignResponse | RedirectResponse:
    campaign = await campaign_service.get_campaign_by_slug(db, slug)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if slug != campaign.slug:
        return RedirectResponse(url=f"/api/v1/campaigns/{campaign.slug}", status_code=301)

    return _to_response(campaign)


@router.patch("/campaigns/{slug}")
async def patch_campaign(
    slug: str,
    body: PatchCampaignRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CampaignResponse:
    campaign = await campaign_service.get_campaign_by_slug(db, slug)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    updated_campaign = await campaign_service.update_campaign(
        db,
        campaign,
        name=body.name,
        description=body.description,
        slug_label=body.slug_label,
    )
    return _to_response(updated_campaign)


@router.delete("/campaigns/{slug}", status_code=204)
async def delete_campaign(
    slug: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    campaign = await campaign_service.get_campaign_by_slug(db, slug)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    await campaign_service.delete_campaign(db, campaign)
