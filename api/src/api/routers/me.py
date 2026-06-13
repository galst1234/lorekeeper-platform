import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models.user import User

router = APIRouter()


class MeResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None


class PatchMeRequest(BaseModel):
    display_name: str

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("display_name cannot be empty")
        if len(v) > 50:
            raise ValueError("display_name cannot exceed 50 characters")
        return v


@router.get("/me")
async def get_me(
    user: Annotated[User, Depends(get_current_user)],
) -> MeResponse:
    return MeResponse(id=user.id, email=user.email, display_name=user.display_name)


@router.patch("/me")
async def patch_me(
    body: PatchMeRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeResponse:
    user.display_name = body.display_name
    await db.commit()
    await db.refresh(user)
    return MeResponse(id=user.id, email=user.email, display_name=user.display_name)
