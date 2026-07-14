from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import CampaignMember
from api.routers._openapi import FORBIDDEN, NOT_FOUND, UNAUTHENTICATED
from api.routers.campaigns.dependencies import require_campaign_member
from api.services import tags as tag_service

router = APIRouter(prefix="/tags", tags=["Tags"])


class CampaignTagsResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"tags": ["magic", "relic", "villain"]}})

    tags: list[str]


@router.get("", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def list_campaign_tags(
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CampaignTagsResponse:
    tags = await tag_service.list_campaign_tags(db, member.campaign_id, member.role)
    return CampaignTagsResponse(tags=tags)
