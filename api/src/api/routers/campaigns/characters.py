from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import ConfigDict, StringConstraints
from pydantic.experimental.missing_sentinel import MISSING
from sqlalchemy.ext.asyncio import AsyncSession

from api.config import settings
from api.database import get_db
from api.models import CampaignMember, Character, CharacterType, MemberRole
from api.routers._openapi import CONFLICT, FORBIDDEN, INVALID_IMAGE, NOT_FOUND, UNAUTHENTICATED
from api.routers.campaigns.dependencies import require_campaign_member
from api.routers.common.campaign_entity import (
    CampaignEntityCreateModel,
    CampaignEntityPatchModel,
    CampaignEntityResponse,
)
from api.services import characters as character_service
from api.services.characters import CharacterSlugConflictError
from api.storage import ALLOWED_IMAGE_CONTENT_TYPES, ImageStorage, get_image_storage

router = APIRouter(prefix="/characters", tags=["Characters"])

_NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class CharacterResponse(CampaignEntityResponse):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "a4c2b1d0-e3f5-4789-abcd-ef0123456789",
                "slug": "elara-moonwhisper",
                "name": "Elara Moonwhisper",
                "character_type": "pc",
                "description": "A wise elven druid from the Emerald Enclave.",
                "restricted": False,
                "tags": ["ally", "spellcaster"],
                "image_url": "/media/3f9c1e2a-3b7e-4a2e-9b1a-9d6a2b0e5c11.jpg",
                "created_at": "2024-01-15T10:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z",
            }
        }
    )

    name: str
    character_type: CharacterType
    description: str | None
    image_url: str | None


class CreateCharacterRequest(CampaignEntityCreateModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "slug": "elara-moonwhisper",
                "name": "Elara Moonwhisper",
                "character_type": "pc",
                "description": "A wise elven druid from the Emerald Enclave.",
                "tags": ["ally", "spellcaster"],
            }
        }
    )

    name: _NonEmptyStr
    character_type: CharacterType
    description: str | None = None


class PatchCharacterRequest(CampaignEntityPatchModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Elara of the Enclave",
                "character_type": "pc",
                "description": "Updated description.",
                "tags": ["ally", "spellcaster"],
            }
        }
    )

    name: _NonEmptyStr | MISSING = MISSING
    character_type: CharacterType | MISSING = MISSING
    description: str | None | MISSING = MISSING


def _to_response(character: Character, image_storage: ImageStorage) -> CharacterResponse:
    return CharacterResponse(
        id=character.id,
        slug=character.slug,
        name=character.name,
        character_type=character.character_type,
        description=character.description,
        restricted=character.restricted,
        tags=character.tags,
        image_url=image_storage.url_for(character.image_key) if character.image_key else None,
        created_at=character.created_at,
        updated_at=character.updated_at,
    )


@router.get("", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def list_characters(
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
    character_type: CharacterType | None = None,
) -> list[CharacterResponse]:
    characters = await character_service.list_characters(db, member.campaign_id, member.role, character_type)
    return [_to_response(character, image_storage) for character in characters]


@router.post("", status_code=201, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND | CONFLICT)
async def create_character(
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    body: CreateCharacterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> CharacterResponse:
    if body.restricted and member.role != MemberRole.GM:
        raise HTTPException(status_code=403, detail="Only the GM can create a restricted character")
    try:
        character = await character_service.create_character(
            db,
            campaign_id=member.campaign_id,
            slug=body.slug,
            name=body.name,
            character_type=body.character_type,
            description=body.description,
            restricted=body.restricted,
            tags=body.tags,
        )
    except CharacterSlugConflictError:
        raise HTTPException(
            status_code=409, detail="A character with that slug already exists in this campaign"
        ) from None
    return _to_response(character, image_storage)


@router.get("/{character_slug}", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def get_character(
    character_slug: str,
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> CharacterResponse:
    character = await character_service.get_character_by_slug(db, member.campaign_id, character_slug, member.role)
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return _to_response(character, image_storage)


@router.patch("/{character_slug}", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def patch_character(
    character_slug: str,
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    body: PatchCharacterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> CharacterResponse:
    if body.restricted is not MISSING and body.restricted and member.role != MemberRole.GM:
        raise HTTPException(status_code=403, detail="Only the GM can mark a character as restricted")
    character = await character_service.get_character_by_slug(
        db, member.campaign_id, character_slug, member.role, for_update=True
    )
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    updated = await character_service.update_character(
        db,
        character,
        name=body.name,
        character_type=body.character_type,
        description=body.description,
        restricted=body.restricted,
        tags=body.tags,
    )
    return _to_response(updated, image_storage)


@router.delete("/{character_slug}", status_code=204, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def delete_character(
    character_slug: str,
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> None:
    character = await character_service.get_character_by_slug(
        db, member.campaign_id, character_slug, member.role, for_update=True
    )
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    await character_service.delete_character(db, character, image_storage)


@router.put("/{character_slug}/image", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND | INVALID_IMAGE)
async def upload_character_image(
    character_slug: str,
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
    file: Annotated[UploadFile, File()],
) -> CharacterResponse:
    character = await character_service.get_character_by_slug(
        db, member.campaign_id, character_slug, member.role, for_update=True
    )
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported image type")
    content = await file.read(settings.image_max_size_bytes + 1)
    if len(content) > settings.image_max_size_bytes:
        raise HTTPException(status_code=400, detail="Image exceeds maximum size")
    new_key = await image_storage.save(content, file.content_type)
    try:
        updated = await character_service.set_character_image(db, character, new_key, image_storage)
    except Exception:
        await image_storage.delete(new_key)
        raise
    return _to_response(updated, image_storage)


@router.delete("/{character_slug}/image", status_code=204, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def delete_character_image(
    character_slug: str,
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
    image_storage: Annotated[ImageStorage, Depends(get_image_storage)],
) -> None:
    character = await character_service.get_character_by_slug(
        db, member.campaign_id, character_slug, member.role, for_update=True
    )
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    await character_service.clear_character_image(db, character, image_storage)
