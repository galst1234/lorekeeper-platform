from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import Campaign
from api.routers._openapi import FORBIDDEN, NOT_FOUND, UNAUTHENTICATED
from api.routers.campaigns.dependencies import require_campaign_owner
from api.services import campaigns as campaign_service

router = APIRouter(prefix="/invites", tags=["Invites"])


class InviteResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "invite_code": "dX9kLmN2pQrS4tUvWxYz",
                "invite_url": "/campaigns/curse-of-strahd-a1b2c3d4/join/dX9kLmN2pQrS4tUvWxYz",
            }
        }
    )

    invite_code: str
    invite_url: str


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
        invite_url=f"/campaigns/{updated.slug}/join/{updated.invite_code}",
    )


@router.delete("", status_code=204, summary="Revoke invite link", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def delete_invite(
    campaign: Annotated[Campaign, Depends(require_campaign_owner)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await campaign_service.revoke_invite(db, campaign)
