import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import Campaign, MemberRole
from api.routers.campaigns.dependencies import require_campaign_member
from api.services import campaigns as campaign_service

router = APIRouter(prefix="/members")


class MemberResponse(BaseModel):
    user_id: uuid.UUID
    display_name: str | None
    role: MemberRole
    joined_at: datetime


@router.get("")
async def list_members(
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MemberResponse]:
    rows = await campaign_service.list_members_with_users(db, campaign.id)
    return [
        MemberResponse(
            user_id=member.user_id,
            display_name=user.display_name,
            role=member.role,
            joined_at=member.joined_at,
        )
        for member, user in rows
    ]
