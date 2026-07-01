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
from api.models import Campaign, MemberRole, User
from api.routers.campaigns.dependencies import (
    get_canonical_campaign,
    require_campaign_owner,
)
from api.services import campaigns as campaign_service

router = APIRouter(prefix="/campaigns")
detail_router = APIRouter(prefix="/{slug}")

_NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
_SlugLabelStr = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(-[a-z0-9]+)*\z",
    ),
]


class CampaignResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    slug: str
    role: MemberRole
    invite_code: str | None
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


def _to_response(
    campaign: Campaign, role: MemberRole = MemberRole.GM, invite_code: str | None = None
) -> CampaignResponse:
    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        slug=campaign.slug,
        role=role,
        invite_code=invite_code,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


@router.get("")
async def list_campaigns(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CampaignResponse]:
    campaigns = await campaign_service.list_campaigns(db, user.id)
    return [_to_response(campaign_with_role.campaign, campaign_with_role.role) for campaign_with_role in campaigns]


@router.post("", status_code=201)
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


@detail_router.get("", response_model=CampaignResponse)
async def get_campaign(
    campaign: Annotated[Campaign, Depends(get_canonical_campaign)],
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CampaignResponse | RedirectResponse:
    role = await campaign_service.get_member_role(db, campaign.id, user.id)
    if role is None:
        raise HTTPException(status_code=403, detail="Forbidden")
    invite_code = campaign.invite_code if role == MemberRole.GM else None
    return _to_response(campaign, role, invite_code=invite_code)


@detail_router.patch("")
async def patch_campaign(
    campaign: Annotated[Campaign, Depends(require_campaign_owner)],
    body: PatchCampaignRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CampaignResponse:
    updated = await campaign_service.update_campaign(
        db,
        campaign,
        name=body.name,
        description=body.description,
        slug_label=body.slug_label,
    )
    return _to_response(updated)


@detail_router.delete("", status_code=204)
async def delete_campaign(
    campaign: Annotated[Campaign, Depends(require_campaign_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await campaign_service.delete_campaign(db, campaign)
