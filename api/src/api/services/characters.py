import uuid

from pydantic_core import MISSING
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Character, CharacterType


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
    name: str,
    character_type: CharacterType,
    description: str | None,
) -> Character:
    character = Character(
        campaign_id=campaign_id,
        name=name,
        character_type=character_type,
        description=description,
    )
    db.add(character)
    await db.flush()
    await db.commit()
    await db.refresh(character)
    return character


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
