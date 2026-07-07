from pathlib import Path

from api.storage import LocalDiskStorage


async def test_save_writes_file_and_returns_key_with_jpeg_extension(tmp_path: Path) -> None:
    image_storage = LocalDiskStorage(root=str(tmp_path))
    key = await image_storage.save(b"fake-jpeg-bytes", "image/jpeg")
    assert key.endswith(".jpg")
    assert (tmp_path / key).read_bytes() == b"fake-jpeg-bytes"


async def test_save_writes_file_with_png_extension(tmp_path: Path) -> None:
    image_storage = LocalDiskStorage(root=str(tmp_path))
    key = await image_storage.save(b"fake-png-bytes", "image/png")
    assert key.endswith(".png")


async def test_save_writes_file_with_webp_extension(tmp_path: Path) -> None:
    image_storage = LocalDiskStorage(root=str(tmp_path))
    key = await image_storage.save(b"fake-webp-bytes", "image/webp")
    assert key.endswith(".webp")


async def test_constructor_creates_root_directory_if_missing(tmp_path: Path) -> None:
    root = tmp_path / "does-not-exist-yet"
    assert not root.exists()
    LocalDiskStorage(root=str(root))
    assert root.exists()


async def test_url_for_returns_relative_media_path(tmp_path: Path) -> None:
    image_storage = LocalDiskStorage(root=str(tmp_path))
    assert image_storage.url_for("abc123.jpg") == "/media/abc123.jpg"


async def test_delete_removes_saved_file(tmp_path: Path) -> None:
    image_storage = LocalDiskStorage(root=str(tmp_path))
    key = await image_storage.save(b"data", "image/jpeg")
    assert (tmp_path / key).exists()
    await image_storage.delete(key)
    assert not (tmp_path / key).exists()


async def test_delete_missing_key_is_noop(tmp_path: Path) -> None:
    image_storage = LocalDiskStorage(root=str(tmp_path))
    await image_storage.delete("nonexistent.jpg")  # must not raise
