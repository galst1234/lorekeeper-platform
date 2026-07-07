from __future__ import annotations

import uuid
from functools import lru_cache
from pathlib import Path
from typing import Protocol

from starlette.concurrency import run_in_threadpool

from api.config import settings

_EXTENSIONS_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

ALLOWED_IMAGE_CONTENT_TYPES = frozenset(_EXTENSIONS_BY_CONTENT_TYPE)


class ImageStorage(Protocol):
    async def save(self, content: bytes, content_type: str) -> str: ...

    async def delete(self, key: str) -> None: ...

    def url_for(self, key: str) -> str: ...


class LocalDiskStorage:
    def __init__(self, root: str) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    async def save(self, content: bytes, content_type: str) -> str:
        extension = _EXTENSIONS_BY_CONTENT_TYPE[content_type]
        key = f"{uuid.uuid4()}{extension}"

        def _write() -> None:
            (self._root / key).write_bytes(content)

        await run_in_threadpool(_write)
        return key

    async def delete(self, key: str) -> None:
        def _delete() -> None:
            (self._root / key).unlink(missing_ok=True)

        await run_in_threadpool(_delete)

    def url_for(self, key: str) -> str:
        return f"/media/{key}"


@lru_cache
def _default_storage() -> ImageStorage:
    return LocalDiskStorage(root=settings.image_upload_dir)


def get_image_storage() -> ImageStorage:
    return _default_storage()
