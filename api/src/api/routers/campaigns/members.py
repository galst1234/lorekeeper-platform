import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import CampaignMember, MemberRole
from api.routers._openapi import FORBIDDEN, NOT_FOUND, UNAUTHENTICATED
from api.routers.campaigns.dependencies import require_campaign_member
from api.services import campaigns as campaign_service

router = APIRouter(prefix="/members", tags=["Members"])


class MemberResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "display_name": "The Dungeon Master",
                "role": "gm",
                "joined_at": "2024-01-15T10:00:00Z",
            }
        }
    )

    user_id: uuid.UUID
    display_name: str | None
    role: MemberRole
    joined_at: datetime


@router.get("", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def list_members(
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MemberResponse]:
    rows = await campaign_service.list_members_with_users(db, member.campaign_id)
    return [
        MemberResponse(
            user_id=member.user_id,
            display_name=user.display_name,
            role=member.role,
            joined_at=member.joined_at,
        )
        for member, user in rows
    ]
