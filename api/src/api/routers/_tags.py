from pydantic import BaseModel, Field, field_validator
from pydantic.experimental.missing_sentinel import MISSING

from api.services.common.tags import TagValidationError, normalize_tags


class TagsCreateModel(BaseModel):
    tags: list[str] = Field(default_factory=list)

    @field_validator("tags")
    @classmethod
    def _normalize_tags(cls, value: list[str]) -> list[str]:
        try:
            return normalize_tags(value)
        except TagValidationError as error:
            raise ValueError(str(error)) from error


class TagsPatchModel(BaseModel):
    tags: list[str] | MISSING = MISSING

    @field_validator("tags")
    @classmethod
    def _normalize_tags(cls, value: list[str] | MISSING) -> list[str] | MISSING:
        if value is MISSING:
            return value
        try:
            return normalize_tags(value)
        except TagValidationError as error:
            raise ValueError(str(error)) from error
