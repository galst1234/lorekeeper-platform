import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from asyncpg import UniqueViolationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Campaign, MemberRole
from api.services import campaigns as campaign_service
from api.services.campaigns import _parse_slug_id
from tests.helpers import make_campaign, make_user

# --- _parse_slug_id ---


def test_parse_slug_id_simple() -> None:
    assert _parse_slug_id("my-campaign-abc12345") == "abc12345"


def test_parse_slug_id_multi_hyphen() -> None:
    assert _parse_slug_id("my-cool-long-campaign-abc12345") == "abc12345"


def test_parse_slug_id_no_label() -> None:
    assert _parse_slug_id("abc12345") == "abc12345"


# --- list_campaigns ---


async def test_list_campaigns_empty(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-list-empty", email="svc-list-empty@test.com")
    result = await campaign_service.list_campaigns(db, user.id)
    assert result == []


async def test_list_campaigns_returns_own(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-list-own", email="svc-list-own@test.com")
    campaign = await make_campaign(db, owner_id=user.id, name="Mine", slug_label="mine", slug_id="own00001")
    result = await campaign_service.list_campaigns(db, user.id)
    assert len(result) == 1
    assert result[0].campaign.id == campaign.id
    assert result[0].campaign.name == "Mine"
    assert result[0].campaign.slug == "mine-own00001"
    assert result[0].role == "gm"


async def test_list_campaigns_excludes_others(db: AsyncSession) -> None:
    other = await make_user(db, supertokens_user_id="svc-list-other", email="svc-list-other@test.com")
    await make_campaign(db, owner_id=other.id, slug_id="other001")
    user = await make_user(db, supertokens_user_id="svc-list-me", email="svc-list-me@test.com")
    result = await campaign_service.list_campaigns(db, user.id)
    assert result == []


async def test_list_campaigns_ordered_newest_first(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-list-ord", email="svc-list-ord@test.com")
    older = await make_campaign(
        db,
        owner_id=user.id,
        slug_id="older001",
        created_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    newer = await make_campaign(
        db,
        owner_id=user.id,
        slug_id="newer001",
        created_at=datetime(2024, 6, 1, tzinfo=UTC),
    )
    result = await campaign_service.list_campaigns(db, user.id)
    assert result[0].campaign.id == newer.id
    assert result[1].campaign.id == older.id


# --- create_campaign ---


async def test_create_campaign_persists(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-create-ok", email="svc-create-ok@test.com")
    campaign = await campaign_service.create_campaign(
        db,
        owner_id=user.id,
        name="Baldur's Gate",
        description="Epic",
        slug_label="baldurs-gate",
    )
    assert campaign.name == "Baldur's Gate"
    assert campaign.description == "Epic"
    assert campaign.slug_label == "baldurs-gate"
    assert len(campaign.slug_id) == 8
    assert campaign.slug.startswith("baldurs-gate-")


async def test_create_campaign_no_description(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-create-nodesc", email="svc-create-nodesc@test.com")
    campaign = await campaign_service.create_campaign(
        db,
        owner_id=user.id,
        name="Minimal",
        description=None,
        slug_label="minimal",
    )
    assert campaign.description is None


async def test_create_campaign_inserts_owner_as_gm(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-cr-gm-usr", email="svc-cr-gm-usr@test.com")
    campaign = await campaign_service.create_campaign(
        db,
        owner_id=user.id,
        name="With GM",
        description=None,
        slug_label="with-gm",
    )
    role = await campaign_service.get_member_role(db, campaign.id, user.id)
    assert role == MemberRole.GM


# --- get_campaign_by_slug ---


async def test_get_campaign_by_slug_found(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-get-ok", email="svc-get-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_label="found", slug_id="getok001")
    result = await campaign_service.get_campaign_by_slug(db, "found-getok001")
    assert result is not None
    assert result.id == campaign.id


async def test_get_campaign_by_slug_not_found(db: AsyncSession) -> None:
    result = await campaign_service.get_campaign_by_slug(db, "anything-notexist")
    assert result is None


async def test_get_campaign_by_slug_uses_slug_id(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-get-stale", email="svc-get-stale@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_label="current-label", slug_id="stale001")
    result = await campaign_service.get_campaign_by_slug(db, "old-label-stale001")
    assert result is not None
    assert result.id == campaign.id
    assert result.slug_label == "current-label"


# --- update_campaign ---


async def test_update_campaign_name(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-upd-name", email="svc-upd-name@test.com")
    campaign = await make_campaign(db, owner_id=user.id, name="Old", slug_label="old", slug_id="upd00001")
    updated = await campaign_service.update_campaign(db, campaign, name="New")
    assert updated.name == "New"
    assert updated.slug_label == "old"


async def test_update_campaign_slug_label(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-upd-slug", email="svc-upd-slug@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_label="original", slug_id="upd00002")
    updated = await campaign_service.update_campaign(db, campaign, slug_label="renamed")
    assert updated.slug_label == "renamed"
    assert updated.slug == "renamed-upd00002"


async def test_update_campaign_clears_description(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-upd-desc", email="svc-upd-desc@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="upd00003", description="Old desc")
    updated = await campaign_service.update_campaign(db, campaign, description=None)
    assert updated.description is None


async def test_update_campaign_missing_fields_not_updated(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-upd-miss", email="svc-upd-miss@test.com")
    campaign = await make_campaign(
        db,
        owner_id=user.id,
        name="Unchanged",
        slug_label="unchanged",
        slug_id="upd00004",
        description="Keep me",
    )
    updated = await campaign_service.update_campaign(db, campaign, slug_label="new-label")
    assert updated.name == "Unchanged"
    assert updated.description == "Keep me"
    assert updated.slug_label == "new-label"


# --- delete_campaign ---


async def test_delete_campaign_removes_record(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-del-ok", email="svc-del-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="del00001")
    await campaign_service.delete_campaign(db, campaign)
    result = await campaign_service.get_campaign_by_slug(db, "test-campaign-del00001")
    assert result is None


# --- create_campaign retry logic (mocked DB) ---


def _unique_violation(constraint_name: str) -> IntegrityError:
    original_error = UniqueViolationError.new(
        {"C": "23505", "M": "duplicate key", "n": constraint_name},
    )
    adapter_error = RuntimeError("asyncpg adapter error")
    adapter_error.__cause__ = original_error
    return IntegrityError(None, None, adapter_error)


async def test_create_campaign_retries_slug_id_collision(monkeypatch: pytest.MonkeyPatch) -> None:
    db = MagicMock(spec=AsyncSession)
    db.flush = AsyncMock(side_effect=[_unique_violation(Campaign.SLUG_ID_UNIQUE_CONSTRAINT), None, None])
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
    assert db.add.call_count == 3
    assert db.flush.await_count == 3
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
    error = _unique_violation(Campaign.SLUG_ID_UNIQUE_CONSTRAINT)
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
