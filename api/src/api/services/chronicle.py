import uuid
from datetime import datetime

from asyncpg import UniqueViolationError
from pydantic_core import MISSING
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from api.models import ChronicleEntry, MemberRole
from api.services.common.visibility import apply_visibility_filter


class EntrySlugConflictError(Exception):
    pass


def _is_slug_conflict(exc: BaseException) -> bool:
    if not isinstance(exc, IntegrityError) or exc.orig is None:
        return False
    original_error = exc.orig.__cause__
    return (
        isinstance(original_error, UniqueViolationError)
        and getattr(original_error, "constraint_name", None) == ChronicleEntry.SLUG_UNIQUE_CONSTRAINT
    )


async def list_entries(db: AsyncSession, campaign_id: uuid.UUID, requester_role: MemberRole) -> list[ChronicleEntry]:
    query = (
        select(ChronicleEntry)
        .where(ChronicleEntry.campaign_id == campaign_id)
        .order_by(ChronicleEntry.occurred_at.desc())
    )
    query = apply_visibility_filter(query, ChronicleEntry, requester_role)
    return list(await db.scalars(query))


async def create_entry(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    slug: str,
    title: str,
    occurred_at: datetime,
    body: str | None,
    author_id: uuid.UUID,
    restricted: bool = False,
    tags: list[str] | None = None,
) -> ChronicleEntry:
    entry = ChronicleEntry(
        campaign_id=campaign_id,
        slug=slug,
        title=title,
        occurred_at=occurred_at,
        body=body,
        author_id=author_id,
        restricted=restricted,
        tags=tags if tags is not None else [],
    )
    try:
        db.add(entry)
        await db.flush()
        await db.commit()
        await db.refresh(entry)
        return entry
    except IntegrityError as exc:
        await db.rollback()
        if _is_slug_conflict(exc):
            raise EntrySlugConflictError() from exc
        raise


async def get_entry_by_slug(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    entry_slug: str,
    requester_role: MemberRole,
) -> ChronicleEntry | None:
    query = (
        select(ChronicleEntry)
        .options(selectinload(ChronicleEntry.author))
        .where(
            ChronicleEntry.campaign_id == campaign_id,
            ChronicleEntry.slug == entry_slug,
        )
        .execution_options(populate_existing=True)
    )
    query = apply_visibility_filter(query, ChronicleEntry, requester_role)
    return await db.scalar(query)


async def update_entry(
    db: AsyncSession,
    entry: ChronicleEntry,
    *,
    title: str | MISSING = MISSING,
    occurred_at: datetime | MISSING = MISSING,
    body: str | None | MISSING = MISSING,
    restricted: bool | MISSING = MISSING,
    tags: list[str] | MISSING = MISSING,
) -> ChronicleEntry:
    if title is not MISSING:
        entry.title = title
    if occurred_at is not MISSING:
        entry.occurred_at = occurred_at
    if body is not MISSING:
        entry.body = body
    if restricted is not MISSING:
        entry.restricted = restricted
    if tags is not MISSING:
        entry.tags = tags
    await db.commit()
    await db.refresh(entry)
    return entry


async def delete_entry(db: AsyncSession, entry: ChronicleEntry) -> None:
    await db.delete(entry)
    await db.commit()
