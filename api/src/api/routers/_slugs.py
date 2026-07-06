from typing import Annotated

from pydantic import BaseModel, StringConstraints, field_validator

_RESERVED_SLUGS = frozenset({"new"})


class NonReservedSlugModel(BaseModel):
    slug: Annotated[str, StringConstraints(min_length=1, max_length=100, pattern=r"^[a-z0-9]+(-[a-z0-9]+)*\z")]

    @field_validator("slug")
    @classmethod
    def _slug_not_reserved(cls, value: str) -> str:
        if value in _RESERVED_SLUGS:
            raise ValueError(f'"{value}" is a reserved slug')
        return value
