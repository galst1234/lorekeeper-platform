import uuid
from datetime import datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints
from pydantic.experimental.missing_sentinel import MISSING
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models import CampaignMember, ChronicleEntry, MemberRole, User
from api.routers._openapi import CONFLICT, FORBIDDEN, NOT_FOUND, UNAUTHENTICATED, UNPROCESSABLE
from api.routers._slugs import NonReservedSlugModel
from api.routers._tags import normalize_tags_or_422
from api.routers.campaigns.dependencies import require_campaign_member
from api.services import chronicle as chronicle_service
from api.services.chronicle import EntrySlugConflictError

router = APIRouter(prefix="/chronicle/entries", tags=["Chronicle"])

_NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class AuthorResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "display_name": "The Dungeon Master",
            }
        }
    )

    id: uuid.UUID
    display_name: str


class ChronicleEntryResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "a4c2b1d0-e3f5-4789-abcd-ef0123456789",
                "slug": "the-fall-of-blackspire",
                "title": "The Fall of Blackspire",
                "occurred_at": "2024-01-15T19:00:00Z",
                "body": "The party stormed the keep at dusk.",
                "restricted": False,
                "tags": ["battle", "turning-point"],
                "created_at": "2024-01-16T02:30:00Z",
                "updated_at": "2024-01-16T02:30:00Z",
            }
        }
    )

    id: uuid.UUID
    slug: str
    title: str
    occurred_at: datetime
    body: str | None
    restricted: bool
    tags: list[str]
    created_at: datetime
    updated_at: datetime


class ChronicleEntryDetailResponse(ChronicleEntryResponse):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "a4c2b1d0-e3f5-4789-abcd-ef0123456789",
                "slug": "the-fall-of-blackspire",
                "title": "The Fall of Blackspire",
                "occurred_at": "2024-01-15T19:00:00Z",
                "body": "The party stormed the keep at dusk.",
                "restricted": False,
                "tags": ["battle", "turning-point"],
                "created_at": "2024-01-16T02:30:00Z",
                "updated_at": "2024-01-16T02:30:00Z",
                "author": {
                    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                    "display_name": "The Dungeon Master",
                },
            }
        }
    )

    author: AuthorResponse | None


class CreateChronicleEntryRequest(NonReservedSlugModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "slug": "the-fall-of-blackspire",
                "title": "The Fall of Blackspire",
                "occurred_at": "2024-01-15T19:00:00Z",
                "body": "The party stormed the keep at dusk.",
                "tags": ["battle", "victory"],
            }
        }
    )

    title: _NonEmptyStr
    occurred_at: AwareDatetime
    body: str | None = None
    restricted: bool = False
    tags: list[str] = Field(default_factory=list)


class PatchChronicleEntryRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "The Fall of Blackspire, Revised",
                "body": "Updated write-up.",
                "tags": ["battle", "turning-point"],
            }
        }
    )

    title: _NonEmptyStr | MISSING = MISSING
    occurred_at: AwareDatetime | MISSING = MISSING
    body: str | None | MISSING = MISSING
    restricted: bool | MISSING = MISSING
    tags: list[str] | MISSING = MISSING


def _to_response(entry: ChronicleEntry) -> ChronicleEntryResponse:
    return ChronicleEntryResponse(
        id=entry.id,
        slug=entry.slug,
        title=entry.title,
        occurred_at=entry.occurred_at,
        body=entry.body,
        restricted=entry.restricted,
        tags=entry.tags,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
    )


def _to_detail_response(entry: ChronicleEntry) -> ChronicleEntryDetailResponse:
    author = None
    if entry.author is not None:
        # display_name is guaranteed non-null once a user can join a campaign (onboarding requires it).
        author = AuthorResponse(id=entry.author.id, display_name=cast(str, entry.author.display_name))
    return ChronicleEntryDetailResponse(
        id=entry.id,
        slug=entry.slug,
        title=entry.title,
        occurred_at=entry.occurred_at,
        body=entry.body,
        restricted=entry.restricted,
        tags=entry.tags,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        author=author,
    )


@router.get("", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def list_chronicle_entries(
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ChronicleEntryResponse]:
    entries = await chronicle_service.list_entries(db, member.campaign_id, member.role)
    return [_to_response(entry) for entry in entries]


@router.post("", status_code=201, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND | CONFLICT | UNPROCESSABLE)
async def create_chronicle_entry(
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    user: Annotated[User, Depends(get_current_user)],
    body: CreateChronicleEntryRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChronicleEntryResponse:
    if body.restricted and member.role != MemberRole.GM:
        raise HTTPException(status_code=403, detail="Only the GM can create a restricted chronicle entry")
    normalized_tags = normalize_tags_or_422(body.tags)
    try:
        entry = await chronicle_service.create_entry(
            db,
            campaign_id=member.campaign_id,
            slug=body.slug,
            title=body.title,
            occurred_at=body.occurred_at,
            body=body.body,
            author_id=user.id,
            restricted=body.restricted,
            tags=normalized_tags,
        )
    except EntrySlugConflictError:
        raise HTTPException(
            status_code=409, detail="A chronicle entry with that slug already exists in this campaign"
        ) from None
    return _to_response(entry)


@router.get("/{entry_slug}", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def get_chronicle_entry(
    entry_slug: str,
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChronicleEntryDetailResponse:
    entry = await chronicle_service.get_entry_by_slug(db, member.campaign_id, entry_slug, member.role)
    if entry is None:
        raise HTTPException(status_code=404, detail="Chronicle entry not found")
    return _to_detail_response(entry)


@router.patch("/{entry_slug}", responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND | UNPROCESSABLE)
async def patch_chronicle_entry(
    entry_slug: str,
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    body: PatchChronicleEntryRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ChronicleEntryResponse:
    if body.restricted is not MISSING and body.restricted and member.role != MemberRole.GM:
        raise HTTPException(status_code=403, detail="Only the GM can mark a chronicle entry as restricted")
    if body.tags is MISSING:
        tags_update: list[str] | MISSING = MISSING
    else:
        tags_update = normalize_tags_or_422(body.tags)
    entry = await chronicle_service.get_entry_by_slug(db, member.campaign_id, entry_slug, member.role)
    if entry is None:
        raise HTTPException(status_code=404, detail="Chronicle entry not found")
    updated = await chronicle_service.update_entry(
        db,
        entry,
        title=body.title,
        occurred_at=body.occurred_at,
        body=body.body,
        restricted=body.restricted,
        tags=tags_update,
    )
    return _to_response(updated)


@router.delete("/{entry_slug}", status_code=204, responses=UNAUTHENTICATED | FORBIDDEN | NOT_FOUND)
async def delete_chronicle_entry(
    entry_slug: str,
    member: Annotated[CampaignMember, Depends(require_campaign_member)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    entry = await chronicle_service.get_entry_by_slug(db, member.campaign_id, entry_slug, member.role)
    if entry is None:
        raise HTTPException(status_code=404, detail="Chronicle entry not found")
    await chronicle_service.delete_entry(db, entry)
