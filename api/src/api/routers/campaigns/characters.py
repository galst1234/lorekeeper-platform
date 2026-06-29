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

router = APIRouter()

_NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class CharacterResponse(BaseModel):
    id: uuid.UUID
    name: str
    character_type: CharacterType
    description: str | None
    created_at: datetime
    updated_at: datetime


class CreateCharacterRequest(BaseModel):
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
        name=character.name,
        character_type=character.character_type,
        description=character.description,
        created_at=character.created_at,
        updated_at=character.updated_at,
    )


@router.get("/campaigns/{slug}/characters")
async def list_characters(
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    character_type: CharacterType | None = None,
) -> list[CharacterResponse]:
    characters = await character_service.list_characters(db, campaign.id, character_type)
    return [_to_response(character) for character in characters]


@router.post("/campaigns/{slug}/characters", status_code=201)
async def create_character(
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    body: CreateCharacterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CharacterResponse:
    character = await character_service.create_character(
        db,
        campaign_id=campaign.id,
        name=body.name,
        character_type=body.character_type,
        description=body.description,
    )
    return _to_response(character)


@router.get("/campaigns/{slug}/characters/{character_id}")
async def get_character(
    character_id: uuid.UUID,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CharacterResponse:
    character = await character_service.get_character(db, campaign.id, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return _to_response(character)


@router.patch("/campaigns/{slug}/characters/{character_id}")
async def patch_character(
    character_id: uuid.UUID,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    body: PatchCharacterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CharacterResponse:
    character = await character_service.get_character(db, campaign.id, character_id)
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


@router.delete("/campaigns/{slug}/characters/{character_id}", status_code=204)
async def delete_character(
    character_id: uuid.UUID,
    campaign: Annotated[Campaign, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    character = await character_service.get_character(db, campaign.id, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    await character_service.delete_character(db, character)
