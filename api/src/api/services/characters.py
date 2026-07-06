import logging
import uuid

from asyncpg import UniqueViolationError
from pydantic_core import MISSING
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Character, CharacterType
from api.storage import ImageStorage

logger = logging.getLogger(__name__)


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
    query = select(Character).where(Character.campaign_id == campaign_id).order_by(Character.name.asc())
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


async def delete_character(db: AsyncSession, character: Character, storage: ImageStorage) -> None:
    image_key = character.image_key
    await db.delete(character)
    await db.commit()
    if image_key is not None:
        try:
            await storage.delete(image_key)
        except OSError:
            logger.warning("Failed to delete image %s for deleted character %s", image_key, character.id)


async def set_character_image(
    db: AsyncSession, character: Character, new_image_key: str, storage: ImageStorage
) -> Character:
    old_key = character.image_key
    character.image_key = new_image_key
    await db.commit()
    await db.refresh(character)
    if old_key is not None:
        try:
            await storage.delete(old_key)
        except OSError:
            logger.warning("Failed to delete old image %s for character %s", old_key, character.id)
    return character


async def clear_character_image(db: AsyncSession, character: Character, storage: ImageStorage) -> Character:
    old_key = character.image_key
    character.image_key = None
    await db.commit()
    await db.refresh(character)
    if old_key is not None:
        try:
            await storage.delete(old_key)
        except OSError:
            logger.warning("Failed to delete old image %s for character %s", old_key, character.id)
    return character
