import secrets
import string
import uuid

from asyncpg import UniqueViolationError
from pydantic_core import MISSING
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, retry_if_exception, stop_after_attempt

from api.models.campaign import SLUG_ID_UNIQUE_CONSTRAINT, Campaign

_SLUG_ID_ALPHABET = string.ascii_lowercase + string.digits


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
        and getattr(original_error, "constraint_name", None) == SLUG_ID_UNIQUE_CONSTRAINT
    )


async def list_campaigns(db: AsyncSession, owner_id: uuid.UUID) -> list[Campaign]:
    result = await db.scalars(
        select(Campaign).where(Campaign.owner_id == owner_id).order_by(Campaign.created_at.desc()),
    )
    return list(result)


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
        await db.commit()
        await db.refresh(campaign)
    except IntegrityError:
        await db.rollback()
        raise

    return campaign


async def get_campaign_by_slug(db: AsyncSession, slug: str) -> Campaign | None:
    slug_id = _parse_slug_id(slug)
    return await db.scalar(select(Campaign).where(Campaign.slug_id == slug_id))


async def patch_campaign(
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


async def delete_campaign(db: AsyncSession, campaign: Campaign) -> None:
    await db.delete(campaign)
    await db.commit()
