import re
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Campaign, CampaignMember, Character, CharacterType, MemberRole, User, UserAuthMethod


async def make_user(
    db: AsyncSession,
    *,
    supertokens_user_id: str,
    email: str,
    display_name: str = "Test User",
) -> User:
    user = User(email=email, display_name=display_name)
    db.add(user)
    await db.flush()
    db.add(UserAuthMethod(user_id=user.id, provider="emailpassword", supertokens_user_id=supertokens_user_id))
    await db.flush()
    return user


async def make_campaign(
    db: AsyncSession,
    *,
    owner_id: uuid.UUID,
    name: str = "Test Campaign",
    slug_label: str = "test-campaign",
    slug_id: str = "aabbccdd",
    description: str | None = None,
    invite_code: str | None = None,
    created_at: datetime | None = None,
) -> Campaign:
    campaign = Campaign(
        owner_id=owner_id,
        name=name,
        description=description,
        slug_label=slug_label,
        slug_id=slug_id,
        invite_code=invite_code,
    )
    if created_at is not None:
        campaign.created_at = created_at
    db.add(campaign)
    await db.flush()
    gm_member = CampaignMember(campaign_id=campaign.id, user_id=owner_id, role=MemberRole.GM)
    db.add(gm_member)
    await db.flush()
    return campaign


async def make_character(
    db: AsyncSession,
    *,
    campaign_id: uuid.UUID,
    name: str = "Test Character",
    slug: str | None = None,
    character_type: CharacterType = CharacterType.PC,
    description: str | None = None,
) -> Character:
    if slug is None:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    character = Character(
        campaign_id=campaign_id,
        slug=slug,
        name=name,
        character_type=character_type,
        description=description,
    )
    db.add(character)
    await db.flush()
    return character


async def make_member(
    db: AsyncSession,
    *,
    campaign_id: uuid.UUID,
    user_id: uuid.UUID,
    role: MemberRole = MemberRole.PLAYER,
) -> CampaignMember:
    member = CampaignMember(campaign_id=campaign_id, user_id=user_id, role=role)
    db.add(member)
    await db.flush()
    return member
