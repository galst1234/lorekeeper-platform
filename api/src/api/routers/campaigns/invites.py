from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models import Campaign, User
from api.routers._openapi import FORBIDDEN, NOT_FOUND, UNAUTHENTICATED
from api.routers.campaigns.campaigns import CampaignResponse, _to_response
from api.routers.campaigns.dependencies import require_campaign_owner
from api.services import campaigns as campaign_service

router = APIRouter(prefix="/invites", tags=["Invites"])


class InviteResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "invite_code": "dX9kLmN2pQrS4tUvWxYz",
                "invite_url": "/campaigns/curse-of-strahd-a1b2c3d4/invites/dX9kLmN2pQrS4tUvWxYz",
            }
        }
    )

    invite_code: str
    invite_url: str


class JoinPreviewResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Curse of Strahd",
                "slug": "curse-of-strahd-a1b2c3d4",
            }
        }
    )

    name: str
    slug: str


@router.post("", summary="Generate invite link", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def create_invite(
    campaign: Annotated[Campaign, Depends(require_campaign_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InviteResponse:
    updated = await campaign_service.generate_invite(db, campaign)
    if updated.invite_code is None:
        raise HTTPException(status_code=500, detail="Failed to generate invite code")
    return InviteResponse(
        invite_code=updated.invite_code,
        invite_url=f"/campaigns/{updated.slug}/invites/{updated.invite_code}",
    )


@router.delete("", status_code=204, summary="Revoke invite link", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def delete_invite(
    campaign: Annotated[Campaign, Depends(require_campaign_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await campaign_service.revoke_invite(db, campaign)


@router.get(
    "/{invite_code}",
    summary="Preview campaign before joining",
    response_model=JoinPreviewResponse,
    responses=UNAUTHENTICATED | NOT_FOUND,
)
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
            url=f"/api/v1/campaigns/{campaign.slug}/invites/{invite_code}",
            status_code=307,
        )
    return JoinPreviewResponse(name=campaign.name, slug=campaign.slug)


@router.post(
    "/{invite_code}",
    summary="Join campaign via invite",
    response_model=CampaignResponse,
    responses=UNAUTHENTICATED | NOT_FOUND,
)
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
            url=f"/api/v1/campaigns/{campaign.slug}/invites/{invite_code}",
            status_code=307,
        )
    joined = await campaign_service.join_campaign(db, campaign, user.id, invite_code)
    if not joined:
        raise HTTPException(status_code=404, detail="Invalid invite")
    role = await campaign_service.get_member_role(db, campaign.id, user.id)
    if role is None:
        raise HTTPException(status_code=500, detail="Membership state error")
    return _to_response(campaign, role)
