from fastapi import HTTPException

from api.services.common.tags import TagValidationError, normalize_tags


def normalize_tags_or_422(raw: list[str]) -> list[str]:
    try:
        return normalize_tags(raw)
    except TagValidationError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
