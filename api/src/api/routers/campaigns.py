import re
import secrets
import string
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from supertokens_python.recipe.session import SessionContainer

from api.auth import get_session, get_user_by_session
from api.database import get_db
from api.models.campaign import Campaign

router = APIRouter()

_SLUG_ID_ALPHABET = string.ascii_lowercase + string.digits


def _generate_slug_id() -> str:
    return "".join(secrets.choice(_SLUG_ID_ALPHABET) for _ in range(8))


def _parse_slug_id(slug: str) -> str:
    return slug.rsplit("-", 1)[-1]


class CampaignResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    slug: str
    created_at: datetime
    updated_at: datetime


class CreateCampaignRequest(BaseModel):
    name: str
    description: str | None = None
    slug_label: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v

    @field_validator("slug_label")
    @classmethod
    def validate_slug_label(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", v):
            raise ValueError(
                "slug_label must be lowercase alphanumeric with hyphens, no leading/trailing or consecutive hyphens"
            )
        return v


class PatchCampaignRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    slug_label: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("name cannot be empty")
        return v

    @field_validator("slug_label")
    @classmethod
    def validate_slug_label(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", v):
            raise ValueError(
                "slug_label must be lowercase alphanumeric with hyphens, no leading/trailing or consecutive hyphens"
            )
        return v


def _to_response(campaign: Campaign) -> CampaignResponse:
    return CampaignResponse(
        id=campaign.id,
        name=campaign.name,
        description=campaign.description,
        slug=campaign.slug,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


@router.get("/campaigns")
async def list_campaigns(
    session: Annotated[SessionContainer, Depends(get_session)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CampaignResponse]:
    user = await get_user_by_session(session, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    result = await db.scalars(select(Campaign).where(Campaign.owner_id == user.id).order_by(Campaign.created_at.desc()))
    return [_to_response(c) for c in result]


@router.post("/campaigns", status_code=201)
async def create_campaign(
    body: CreateCampaignRequest,
    session: Annotated[SessionContainer, Depends(get_session)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CampaignResponse:
    user = await get_user_by_session(session, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    for _ in range(5):
        slug_id = _generate_slug_id()
        campaign = Campaign(
            owner_id=user.id,
            name=body.name,
            description=body.description,
            slug_label=body.slug_label,
            slug_id=slug_id,
        )
        db.add(campaign)
        try:
            await db.flush()
            await db.commit()
            await db.refresh(campaign)
            return _to_response(campaign)
        except IntegrityError:
            await db.rollback()

    raise HTTPException(status_code=500, detail="Failed to generate unique slug_id")
