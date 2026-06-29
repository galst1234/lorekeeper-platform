import uuid

from asyncpg import UniqueViolationError
from pydantic_core import MISSING
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Character, CharacterType


class CharacterSlugConflictError(Exception):
    pass


def _is_slug_conflict(exc: BaseException) -> bool:
    if not isinstance(exc, IntegrityError) or exc.orig is None:
        return False
    original_error = exc.orig.__cause__
    return (
        isinstance(original_error, UniqueViolationError)
        and getattr(original_error, "constraint_name", None) == Character.SLUG_UNIQUE_CONSTRAINT
    )


async def list_characters(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    character_type: CharacterType | None = None,
) -> list[Character]:
    query = select(Character).where(Character.campaign_id == campaign_id).order_by(Character.created_at.asc())
    if character_type is not None:
        query = query.where(Character.character_type == character_type)
    return list(await db.scalars(query))


async def create_character(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    slug: str,
    name: str,
    character_type: CharacterType,
    description: str | None,
) -> Character:
    character = Character(
        campaign_id=campaign_id,
        slug=slug,
        name=name,
        character_type=character_type,
        description=description,
    )
    try:
        db.add(character)
        await db.flush()
        await db.commit()
        await db.refresh(character)
        return character
    except IntegrityError as exc:
        await db.rollback()
        if _is_slug_conflict(exc):
            raise CharacterSlugConflictError() from exc
        raise


async def get_character(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    character_id: uuid.UUID,
) -> Character | None:
    return await db.scalar(
        select(Character).where(
            Character.id == character_id,
            Character.campaign_id == campaign_id,
        )
    )


async def get_character_by_slug(
    db: AsyncSession,
    campaign_id: uuid.UUID,
    character_slug: str,
) -> Character | None:
    return await db.scalar(
        select(Character).where(
            Character.campaign_id == campaign_id,
            Character.slug == character_slug,
        )
    )


async def update_character(
    db: AsyncSession,
    character: Character,
    *,
    name: str | MISSING = MISSING,
    character_type: CharacterType | MISSING = MISSING,
    description: str | None | MISSING = MISSING,
) -> Character:
    if name is not MISSING:
        character.name = name
    if character_type is not MISSING:
        character.character_type = character_type
    if description is not MISSING:
        character.description = description
    await db.commit()
    await db.refresh(character)
    return character


async def delete_character(db: AsyncSession, character: Character) -> None:
    await db.delete(character)
    await db.commit()
