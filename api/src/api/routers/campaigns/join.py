from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models import User
from api.routers.campaigns.campaigns import CampaignResponse, _to_response
from api.services import campaigns as campaign_service

router = APIRouter(prefix="/join")


class JoinPreviewResponse(BaseModel):
    name: str
    slug: str


@router.get("/{invite_code}", response_model=JoinPreviewResponse)
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


@router.post("/{invite_code}", response_model=CampaignResponse)
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
