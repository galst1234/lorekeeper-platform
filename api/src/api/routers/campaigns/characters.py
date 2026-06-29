import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, StringConstraints
from pydantic.experimental.missing_sentinel import MISSING
from sqlalchemy.ext.asyncio import AsyncSession

from api.database import get_db
from api.models import Campaign, Character, CharacterType
from api.routers.campaigns.dependencies import require_campaign_member
from api.services import characters as character_service
from api.services.characters import CharacterSlugConflictError

router = APIRouter(prefix="/characters")

_NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
_CharacterSlugStr = Annotated[
    str,
    StringConstraints(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(-[a-z0-9]+)*\z",
    ),
]


class CharacterResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    character_type: CharacterType
    description: str | None
    created_at: datetime
    updated_at: datetime


class CreateCharacterRequest(BaseModel):
    slug: _CharacterSlugStr
    name: _NonEmptyStr
    character_type: CharacterType
    description: str | None = None


class PatchCharacterRequest(BaseModel):
    name: _NonEmptyStr | MISSING = MISSING
    character_type: CharacterType | MISSING = MISSING
    description: str | None | MISSING = MISSING


def _to_response(character: Character) -> CharacterResponse:
    return CharacterResponse(
        id=character.id,
        slug=character.slug,
        name=character.name,
        character_type=character.character_type,
        description=character.description,
        created_at=character.created_at,
        updated_at=character.updated_at,
    )


@router.get("")
async def list_characters(
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    character_type: CharacterType | None = None,
) -> list[CharacterResponse]:
    characters = await character_service.list_characters(db, campaign.id, character_type)
    return [_to_response(character) for character in characters]


@router.post("", status_code=201)
async def create_character(
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    body: CreateCharacterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CharacterResponse:
    try:
        character = await character_service.create_character(
            db,
            campaign_id=campaign.id,
            slug=body.slug,
            name=body.name,
            character_type=body.character_type,
            description=body.description,
        )
    except CharacterSlugConflictError:
        raise HTTPException(
            status_code=409, detail="A character with that slug already exists in this campaign"
        ) from None
    return _to_response(character)


@router.get("/{character_slug}")
async def get_character(
    character_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CharacterResponse:
    character = await character_service.get_character_by_slug(db, campaign.id, character_slug)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return _to_response(character)


@router.patch("/{character_slug}")
async def patch_character(
    character_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    body: PatchCharacterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CharacterResponse:
    character = await character_service.get_character_by_slug(db, campaign.id, character_slug)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    updated = await character_service.update_character(
        db,
        character,
        name=body.name,
        character_type=body.character_type,
        description=body.description,
    )
    return _to_response(updated)


@router.delete("/{character_slug}", status_code=204)
async def delete_character(
    character_slug: str,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    character = await character_service.get_character_by_slug(db, campaign.id, character_slug)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    await character_service.delete_character(db, character)
