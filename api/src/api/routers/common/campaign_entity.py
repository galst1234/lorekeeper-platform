import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints, field_validator
from pydantic.experimental.missing_sentinel import MISSING

from api.services.common.tags import TagValidationError, normalize_tags

_RESERVED_SLUGS = frozenset({"new"})


class CampaignEntityCreateModel(BaseModel):
    slug: Annotated[str, StringConstraints(min_length=1, max_length=100, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*\z")]
    tags: list[str] = Field(default_factory=list)
    restricted: bool = False

    @field_validator("slug")
    @classmethod
    def _slug_not_reserved(cls, value: str) -> str:
        if value in _RESERVED_SLUGS:
            raise ValueError(f'"{value}" is a reserved slug')
        return value

    @field_validator("tags")
    @classmethod
    def _normalize_tags(cls, value: list[str]) -> list[str]:
        try:
            return normalize_tags(value)
        except TagValidationError as error:
            raise ValueError(str(error)) from error


class CampaignEntityPatchModel(BaseModel):
    tags: list[str] | MISSING = MISSING
    restricted: bool | MISSING = MISSING

    @field_validator("tags")
    @classmethod
    def _normalize_tags(cls, value: list[str] | MISSING) -> list[str] | MISSING:
        if value is MISSING:
            return value
        try:
            return normalize_tags(value)
        except TagValidationError as error:
            raise ValueError(str(error)) from error


class CampaignEntityResponse(BaseModel):
    id: uuid.UUID
    slug: str
    restricted: bool
    tags: list[str]
    created_at: datetime
    updated_at: datetime
