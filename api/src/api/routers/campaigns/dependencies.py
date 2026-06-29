from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models import Campaign, User
from api.services import campaigns as campaign_service


async def get_campaign_or_404(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Campaign:
    campaign = await campaign_service.get_campaign_by_slug(db, slug)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


async def get_canonical_campaign(
    slug: str,
    campaign: Annotated[Campaign, Depends(get_campaign_or_404)],
) -> Campaign:
    if slug != campaign.slug:
        raise HTTPException(status_code=307, headers={"Location": f"/api/v1/campaigns/{campaign.slug}"})
    return campaign


async def require_campaign_owner(
    campaign: Annotated[Campaign, Depends(get_campaign_or_404)],
    user: Annotated[User, Depends(get_current_user)],
) -> Campaign:
    if campaign.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return campaign


async def require_campaign_member(
    campaign: Annotated[Campaign, Depends(get_campaign_or_404)],
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Campaign:
    if not await campaign_service.is_member(db, campaign.id, user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return campaign
