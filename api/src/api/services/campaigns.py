import logging
import secrets
import string
import uuid
from dataclasses import dataclass

from asyncpg import UniqueViolationError
from pydantic_core import MISSING
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, retry_if_exception, stop_after_attempt

from api.models import Campaign, CampaignMember, Character, Item, MemberRole, User
from api.storage import ImageStorage

_SLUG_ID_ALPHABET = string.ascii_lowercase + string.digits

logger = logging.getLogger(__name__)


@dataclass
class CampaignWithRole:
    campaign: Campaign
    role: MemberRole


def _generate_slug_id() -> str:
    return "".join(secrets.choice(_SLUG_ID_ALPHABET) for _ in range(8))


def _parse_slug_id(slug: str) -> str:
    return slug.rsplit("-", 1)[-1]


def _is_slug_id_collision(exc: BaseException) -> bool:
    if not isinstance(exc, IntegrityError) or exc.orig is None:
        return False

    original_error = exc.orig.__cause__
    return (
        isinstance(original_error, UniqueViolationError)
        and getattr(original_error, "constraint_name", None) == Campaign.SLUG_ID_UNIQUE_CONSTRAINT
    )


async def list_campaigns(db: AsyncSession, user_id: uuid.UUID) -> list[CampaignWithRole]:
    rows = list(
        await db.execute(
            select(Campaign, CampaignMember.role)
            .join(
                CampaignMember,
                (Campaign.id == CampaignMember.campaign_id) & (CampaignMember.user_id == user_id),
            )
            .order_by(Campaign.created_at.desc())
        )
    )
    return [CampaignWithRole(campaign=campaign, role=role) for campaign, role in rows]


@retry(
    retry=retry_if_exception(_is_slug_id_collision),
    stop=stop_after_attempt(5),
    reraise=True,
)
async def create_campaign(
    db: AsyncSession,
    owner_id: uuid.UUID,
    name: str,
    description: str | None,
    slug_label: str,
) -> Campaign:
    campaign = Campaign(
        owner_id=owner_id,
        name=name,
        description=description,
        slug_label=slug_label,
        slug_id=_generate_slug_id(),
    )
    db.add(campaign)
    try:
        await db.flush()
        db.add(CampaignMember(campaign_id=campaign.id, user_id=owner_id, role=MemberRole.GM))
        await db.flush()
        await db.commit()
        await db.refresh(campaign)
    except IntegrityError:
        await db.rollback()
        raise

    return campaign


async def get_campaign_by_slug(db: AsyncSession, slug: str) -> Campaign | None:
    slug_id = _parse_slug_id(slug)
    return await db.scalar(select(Campaign).where(Campaign.slug_id == slug_id))


async def update_campaign(
    db: AsyncSession,
    campaign: Campaign,
    *,
    name: str | MISSING = MISSING,
    description: str | None | MISSING = MISSING,
    slug_label: str | MISSING = MISSING,
) -> Campaign:
    if name is not MISSING:
        campaign.name = name
    if description is not MISSING:
        campaign.description = description
    if slug_label is not MISSING:
        campaign.slug_label = slug_label

    await db.commit()
    await db.refresh(campaign)
    return campaign


async def delete_campaign(db: AsyncSession, campaign: Campaign, storage: ImageStorage) -> None:
    character_keys = [
        key
        for key in await db.scalars(
            select(Character.image_key).where(Character.campaign_id == campaign.id, Character.image_key.is_not(None))
        )
        if key is not None
    ]
    item_keys = [
        key
        for key in await db.scalars(
            select(Item.image_key).where(Item.campaign_id == campaign.id, Item.image_key.is_not(None))
        )
        if key is not None
    ]
    await db.delete(campaign)
    await db.commit()
    for key in [*character_keys, *item_keys]:
        try:
            await storage.delete(key)
        except Exception:
            logger.warning("Failed to delete orphaned image %s for campaign %s", key, campaign.id)


def _generate_invite_code() -> str:
    return secrets.token_urlsafe(24)


async def generate_invite(db: AsyncSession, campaign: Campaign) -> Campaign:
    new_code = _generate_invite_code()
    await db.execute(
        update(Campaign).where(Campaign.id == campaign.id, Campaign.invite_code.is_(None)).values(invite_code=new_code)
    )
    await db.commit()
    await db.refresh(campaign)
    return campaign


async def revoke_invite(db: AsyncSession, campaign: Campaign) -> None:
    campaign.invite_code = None
    await db.commit()


async def join_campaign(db: AsyncSession, campaign: Campaign, user_id: uuid.UUID, invite_code: str) -> bool:
    """Returns False if the invite code was revoked before the insert could complete."""
    campaign_id = campaign.id  # PK is always retained in the identity map
    # Lock and re-validate the invite code atomically to close the revoke-then-join race window
    locked = await db.scalar(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.invite_code == invite_code).with_for_update()
    )
    if locked is None:
        return False
    query = (
        pg_insert(CampaignMember)
        .values(campaign_id=campaign_id, user_id=user_id, role=MemberRole.PLAYER)
        .on_conflict_do_nothing()
    )
    await db.execute(query)
    await db.commit()
    return True


async def list_members(db: AsyncSession, campaign_id: uuid.UUID) -> list[CampaignMember]:
    return list(
        await db.scalars(
            select(CampaignMember).where(CampaignMember.campaign_id == campaign_id),
        )
    )


async def list_members_with_users(db: AsyncSession, campaign_id: uuid.UUID) -> list[tuple[CampaignMember, User]]:
    rows = await db.execute(
        select(CampaignMember, User)
        .join(User, CampaignMember.user_id == User.id)
        .where(CampaignMember.campaign_id == campaign_id)
        .order_by(CampaignMember.role, User.display_name),
    )
    return list(rows.tuples())


async def is_member(db: AsyncSession, campaign_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    return (
        await db.scalar(
            select(CampaignMember).where(
                CampaignMember.campaign_id == campaign_id,
                CampaignMember.user_id == user_id,
            )
        )
        is not None
    )


async def get_member_role(db: AsyncSession, campaign_id: uuid.UUID, user_id: uuid.UUID) -> MemberRole | None:
    return await db.scalar(
        select(CampaignMember.role).where(
            CampaignMember.campaign_id == campaign_id,
            CampaignMember.user_id == user_id,
        )
    )
