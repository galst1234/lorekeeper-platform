from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models import Campaign, User
from api.services import campaigns as campaign_service


async def require_campaign_member(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Campaign:
    campaign = await campaign_service.get_campaign_by_slug(db, slug)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    if not await campaign_service.is_member(db, campaign.id, user.id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return campaign
