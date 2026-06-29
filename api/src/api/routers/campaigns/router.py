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
from api.routers.campaigns import characters
from api.services import campaigns as campaign_service

router = APIRouter(prefix="/campaigns")

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


class InviteResponse(BaseModel):
    invite_code: str
    invite_url: str


class JoinPreviewResponse(BaseModel):
    name: str
    slug: str


def _to_response(campaign: Campaign, role: MemberRole = MemberRole.GM) -> CampaignResponse:
    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        slug=campaign.slug,
        role=role,
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


@router.get("/{slug}", response_model=CampaignResponse)
async def get_campaign(
    slug: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CampaignResponse | RedirectResponse:
    campaign = await campaign_service.get_campaign_by_slug(db, slug)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    role = await campaign_service.get_member_role(db, campaign.id, user.id)
    if role is None:
        raise HTTPException(status_code=403, detail="Forbidden")
    if slug != campaign.slug:
        return RedirectResponse(url=f"/api/v1/campaigns/{campaign.slug}", status_code=307)
    return _to_response(campaign, role)


@router.patch("/{slug}")
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


@router.delete("/{slug}", status_code=204)
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


@router.post("/{slug}/invite")
async def create_invite(
    slug: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InviteResponse:
    campaign = await campaign_service.get_campaign_by_slug(db, slug)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    campaign = await campaign_service.generate_invite(db, campaign)
    if campaign.invite_code is None:
        raise HTTPException(status_code=500, detail="Failed to generate invite code")
    return InviteResponse(
        invite_code=campaign.invite_code,
        invite_url=f"/campaigns/{campaign.slug}/join/{campaign.invite_code}",
    )


@router.delete("/{slug}/invite", status_code=204)
async def delete_invite(
    slug: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    campaign = await campaign_service.get_campaign_by_slug(db, slug)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if campaign.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    await campaign_service.revoke_invite(db, campaign)


@router.get("/{slug}/join/{invite_code}", response_model=JoinPreviewResponse)
async def get_join_preview(
    slug: str,
    invite_code: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JoinPreviewResponse | RedirectResponse:
    campaign = await campaign_service.get_campaign_by_slug(db, slug)
    if campaign is None or campaign.invite_code is None or campaign.invite_code != invite_code:
        raise HTTPException(status_code=404, detail="Invalid invite")
    if slug != campaign.slug:
        return RedirectResponse(
            url=f"/api/v1/campaigns/{campaign.slug}/join/{invite_code}",
            status_code=307,
        )
    return JoinPreviewResponse(name=campaign.name, slug=campaign.slug)


@router.post("/{slug}/join/{invite_code}", response_model=CampaignResponse)
async def join_campaign(
    slug: str,
    invite_code: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CampaignResponse | RedirectResponse:
    campaign = await campaign_service.get_campaign_by_slug(db, slug)
    if campaign is None or campaign.invite_code is None or campaign.invite_code != invite_code:
        raise HTTPException(status_code=404, detail="Invalid invite")
    if slug != campaign.slug:
        return RedirectResponse(
            url=f"/api/v1/campaigns/{campaign.slug}/join/{invite_code}",
            status_code=307,
        )
    joined = await campaign_service.join_campaign(db, campaign, user.id, invite_code)
    if not joined:
        raise HTTPException(status_code=404, detail="Invalid invite")
    role = await campaign_service.get_member_role(db, campaign.id, user.id)
    if role is None:
        raise HTTPException(status_code=500, detail="Membership state error")
    return _to_response(campaign, role)


router.include_router(characters.router)
