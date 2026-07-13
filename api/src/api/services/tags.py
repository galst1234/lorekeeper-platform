import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Character, ChronicleEntry, Item, Location, MemberRole
from api.services.common.visibility import apply_visibility_filter

_TAGGED_MODELS = (Character, Item, Location, ChronicleEntry)


async def list_campaign_tags(db: AsyncSession, campaign_id: uuid.UUID, requester_role: MemberRole) -> list[str]:
    tags: set[str] = set()
    for model in _TAGGED_MODELS:
        query = select(func.unnest(model.tags)).where(model.campaign_id == campaign_id)
        query = apply_visibility_filter(query, model, requester_role)
        tags.update(await db.scalars(query))
    return sorted(tags)
