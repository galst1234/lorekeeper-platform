import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from api.database import get_db
from api.models import User
from api.routers._openapi import UNAUTHENTICATED

router = APIRouter(tags=["Me"])


class MeResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "email": "dungeonmaster@example.com",
                "display_name": "The Dungeon Master",
            }
        }
    )

    id: uuid.UUID
    email: str
    display_name: str | None


class PatchMeRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"display_name": "The Dungeon Master"}})

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


@router.get("/me", responses=UNAUTHENTICATED)
async def get_me(
    user: Annotated[User, Depends(get_current_user)],
) -> MeResponse:
    return MeResponse(id=user.id, email=user.email, display_name=user.display_name)


@router.patch("/me", responses=UNAUTHENTICATED)
async def patch_me(
    body: PatchMeRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeResponse:
    user.display_name = body.display_name
    await db.commit()
    await db.refresh(user)
    return MeResponse(id=user.id, email=user.email, display_name=user.display_name)
