import logging
import uuid

from asyncpg import UniqueViolationError
from pydantic_core import MISSING
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Item, MemberRole
from api.services.common.visibility import apply_visibility_filter
from api.storage import ImageStorage

logger = logging.getLogger(__name__)


class ItemSlugConflictError(Exception):
    pass


def _is_slug_conflict(exc: BaseException) -> bool:
    if not isinstance(exc, IntegrityError) or exc.orig is None:
        return False
    original_error = exc.orig.__cause__
    return (
        isinstance(original_error, UniqueViolationError)
        and getattr(original_error, "constraint_name", None) == Item.SLUG_UNIQUE_CONSTRAINT
    )


async def list_items(db: AsyncSession, campaign_id: uuid.UUID, requester_role: MemberRole) -> list[Item]:
    query = select(Item).where(Item.campaign_id == campaign_id).order_by(Item.name.asc())
    query = apply_visibility_filter(query, Item, requester_role)
    return list(await db.scalars(query))


async def create_item(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    slug: str,
    name: str,
    description: str | None,
    restricted: bool = False,
    tags: list[str] | None = None,
) -> Item:
    item = Item(
        campaign_id=campaign_id,
        slug=slug,
        name=name,
        description=description,
        restricted=restricted,
        tags=tags if tags is not None else [],
    )
    try:
        db.add(item)
        await db.flush()
        await db.commit()
        await db.refresh(item)
        return item
    except IntegrityError as exc:
        await db.rollback()
        if _is_slug_conflict(exc):
            raise ItemSlugConflictError() from exc
        raise


async def get_item_by_slug(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    item_slug: str,
    requester_role: MemberRole,
) -> Item | None:
    query = select(Item).where(
        Item.campaign_id == campaign_id,
        Item.slug == item_slug,
    )
    query = apply_visibility_filter(query, Item, requester_role)
    return await db.scalar(query)


async def update_item(
    db: AsyncSession,
    item: Item,
    *,
    name: str | MISSING = MISSING,
    description: str | None | MISSING = MISSING,
    restricted: bool | MISSING = MISSING,
    tags: list[str] | MISSING = MISSING,
) -> Item:
    if name is not MISSING:
        item.name = name
    if description is not MISSING:
        item.description = description
    if restricted is not MISSING:
        item.restricted = restricted
    if tags is not MISSING:
        item.tags = tags
    await db.commit()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item: Item, image_storage: ImageStorage) -> None:
    image_key = item.image_key
    await db.delete(item)
    await db.commit()
    if image_key is not None:
        try:
            await image_storage.delete(image_key)
        except Exception:
            logger.warning("Failed to delete image %s for deleted item %s", image_key, item.id)


async def list_item_image_keys(db: AsyncSession, campaign_id: uuid.UUID) -> list[str]:
    return [
        key
        for key in await db.scalars(
            select(Item.image_key).where(Item.campaign_id == campaign_id, Item.image_key.is_not(None))
        )
        if key is not None
    ]


async def set_item_image(db: AsyncSession, item: Item, new_image_key: str, image_storage: ImageStorage) -> Item:
    old_key = item.image_key
    item.image_key = new_image_key
    await db.commit()
    try:
        await db.refresh(item)
    except Exception:
        logger.warning("Failed to refresh item %s after image update", item.id)
    if old_key is not None:
        try:
            await image_storage.delete(old_key)
        except Exception:
            logger.warning("Failed to delete old image %s for item %s", old_key, item.id)
    return item


async def clear_item_image(db: AsyncSession, item: Item, image_storage: ImageStorage) -> Item:
    old_key = item.image_key
    item.image_key = None
    await db.commit()
    try:
        await db.refresh(item)
    except Exception:
        logger.warning("Failed to refresh item %s after image update", item.id)
    if old_key is not None:
        try:
            await image_storage.delete(old_key)
        except Exception:
            logger.warning("Failed to delete old image %s for item %s", old_key, item.id)
    return item
