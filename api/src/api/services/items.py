import uuid

from asyncpg import UniqueViolationError
from pydantic_core import MISSING
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Item


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


async def list_items(db: AsyncSession, campaign_id: uuid.UUID) -> list[Item]:
    query = select(Item).where(Item.campaign_id == campaign_id).order_by(Item.name.asc())
    return list(await db.scalars(query))


async def create_item(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    slug: str,
    name: str,
    description: str | None,
) -> Item:
    item = Item(
        campaign_id=campaign_id,
        slug=slug,
        name=name,
        description=description,
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
) -> Item | None:
    return await db.scalar(
        select(Item).where(
            Item.campaign_id == campaign_id,
            Item.slug == item_slug,
        )
    )


async def update_item(
    db: AsyncSession,
    item: Item,
    *,
    name: str | MISSING = MISSING,
    description: str | None | MISSING = MISSING,
) -> Item:
    if name is not MISSING:
        item.name = name
    if description is not MISSING:
        item.description = description
    await db.commit()
    await db.refresh(item)
    return item


async def delete_item(db: AsyncSession, item: Item) -> None:
    await db.delete(item)
    await db.commit()
