import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from asyncpg import UniqueViolationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.campaign import SLUG_ID_UNIQUE_CONSTRAINT
from api.services import campaigns as campaign_service


def _unique_violation(constraint_name: str) -> IntegrityError:
    original_error = UniqueViolationError.new(
        {"C": "23505", "M": "duplicate key", "n": constraint_name},
    )
    adapter_error = RuntimeError("asyncpg adapter error")
    adapter_error.__cause__ = original_error
    return IntegrityError(None, None, adapter_error)


async def test_create_campaign_retries_slug_id_collision(monkeypatch: pytest.MonkeyPatch) -> None:
    db = MagicMock(spec=AsyncSession)
    db.flush = AsyncMock(side_effect=[_unique_violation(SLUG_ID_UNIQUE_CONSTRAINT), None])
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()
    slug_ids = iter(["collision", "unique01"])
    monkeypatch.setattr(campaign_service, "_generate_slug_id", lambda: next(slug_ids))

    campaign = await campaign_service.create_campaign(
        db,
        owner_id=uuid.uuid4(),
        name="Test",
        description=None,
        slug_label="test",
    )

    assert campaign.slug_id == "unique01"
    assert db.add.call_count == 2
    assert db.flush.await_count == 2
    db.rollback.assert_awaited_once()


async def test_create_campaign_does_not_retry_other_unique_violation() -> None:
    db = MagicMock(spec=AsyncSession)
    error = _unique_violation("other_unique_constraint")
    db.flush = AsyncMock(side_effect=error)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()

    with pytest.raises(IntegrityError) as exc_info:
        await campaign_service.create_campaign(
            db,
            owner_id=uuid.uuid4(),
            name="Test",
            description=None,
            slug_label="test",
        )

    assert exc_info.value is error
    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()


async def test_create_campaign_reraises_integrity_error_after_five_collisions() -> None:
    db = MagicMock(spec=AsyncSession)
    error = _unique_violation(SLUG_ID_UNIQUE_CONSTRAINT)
    db.flush = AsyncMock(side_effect=error)
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.rollback = AsyncMock()

    with pytest.raises(IntegrityError) as exc_info:
        await campaign_service.create_campaign(
            db,
            owner_id=uuid.uuid4(),
            name="Test",
            description=None,
            slug_label="test",
        )

    assert exc_info.value is error
    assert db.flush.await_count == 5
    assert db.rollback.await_count == 5
    db.commit.assert_not_awaited()
