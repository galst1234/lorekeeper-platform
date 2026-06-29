import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, StringConstraints
from pydantic.experimental.missing_sentinel import MISSING
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models import Campaign, Character, CharacterType, User
from api.services import campaigns as campaign_service
from api.services import characters as character_service

router = APIRouter()

_NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class CharacterResponse(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
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
        campaign_id=character.campaign_id,
        name=character.name,
        character_type=character.character_type,
        description=character.description,
        created_at=character.created_at,
        updated_at=character.updated_at,
    )


async def _get_campaign_or_404(slug: str, db: AsyncSession) -> Campaign:
    campaign = await campaign_service.get_campaign_by_slug(db, slug)
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


async def _assert_member(db: AsyncSession, campaign_id: uuid.UUID, user_id: uuid.UUID) -> None:
    if not await campaign_service.is_member(db, campaign_id, user_id):
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/campaigns/{slug}/characters")
async def list_characters(
    slug: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    character_type: CharacterType | None = None,
) -> list[CharacterResponse]:
    campaign = await _get_campaign_or_404(slug, db)
    await _assert_member(db, campaign.id, user.id)
    characters = await character_service.list_characters(db, campaign.id, character_type)
    return [_to_response(character) for character in characters]


@router.post("/campaigns/{slug}/characters", status_code=201)
async def create_character(
    slug: str,
    body: CreateCharacterRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CharacterResponse:
    campaign = await _get_campaign_or_404(slug, db)
    await _assert_member(db, campaign.id, user.id)
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
    slug: str,
    character_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CharacterResponse:
    campaign = await _get_campaign_or_404(slug, db)
    await _assert_member(db, campaign.id, user.id)
    character = await character_service.get_character(db, campaign.id, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return _to_response(character)


@router.patch("/campaigns/{slug}/characters/{character_id}")
async def patch_character(
    slug: str,
    character_id: uuid.UUID,
    body: PatchCharacterRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CharacterResponse:
    campaign = await _get_campaign_or_404(slug, db)
    await _assert_member(db, campaign.id, user.id)
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
    slug: str,
    character_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    campaign = await _get_campaign_or_404(slug, db)
    await _assert_member(db, campaign.id, user.id)
    character = await character_service.get_character(db, campaign.id, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    await character_service.delete_character(db, character)
