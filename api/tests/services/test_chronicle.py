from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from api.models import MemberRole
from api.services import chronicle as chronicle_service
from api.services.chronicle import EntrySlugConflictError
from tests.helpers import make_campaign, make_chronicle_entry, make_user

# --- list_entries ---


async def test_list_entries_empty(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-list-empty", email="svc-chr-list-empty@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrl0001")
    result = await chronicle_service.list_entries(db, campaign.id, MemberRole.GM)
    assert result == []


async def test_list_entries_returns_all(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-list-all", email="svc-chr-list-all@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrl0002")
    first = await make_chronicle_entry(db, campaign_id=campaign.id, slug="first", title="First")
    second = await make_chronicle_entry(db, campaign_id=campaign.id, slug="second", title="Second")
    result = await chronicle_service.list_entries(db, campaign.id, MemberRole.GM)
    ids = [entry.id for entry in result]
    assert first.id in ids
    assert second.id in ids


async def test_list_entries_orders_by_occurred_at_desc(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-list-ord", email="svc-chr-list-ord@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrl0003")
    recent_session = await make_chronicle_entry(
        db, campaign_id=campaign.id, slug="session-two", occurred_at=datetime(2024, 2, 1, tzinfo=UTC)
    )
    backfilled_older_session = await make_chronicle_entry(
        db, campaign_id=campaign.id, slug="session-one", occurred_at=datetime(2024, 1, 1, tzinfo=UTC)
    )
    result = await chronicle_service.list_entries(db, campaign.id, MemberRole.GM)
    assert result[0].id == recent_session.id
    assert result[1].id == backfilled_older_session.id


async def test_list_entries_excludes_other_campaign(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-list-iso", email="svc-chr-list-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="chrla001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="chrlb001")
    await make_chronicle_entry(db, campaign_id=campaign_b.id, title="Other")
    result = await chronicle_service.list_entries(db, campaign_a.id, MemberRole.GM)
    assert result == []


# --- create_entry ---


async def test_create_entry_persists(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-cr-ok", email="svc-chr-cr-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrc0001")
    occurred_at = datetime(2024, 1, 15, 19, 0, tzinfo=UTC)
    entry = await chronicle_service.create_entry(
        db,
        campaign_id=campaign.id,
        slug="the-fall-of-blackspire",
        title="The Fall of Blackspire",
        occurred_at=occurred_at,
        body="The party stormed the keep at dusk.",
        author_id=user.id,
    )
    assert entry.slug == "the-fall-of-blackspire"
    assert entry.title == "The Fall of Blackspire"
    assert entry.occurred_at == occurred_at
    assert entry.body == "The party stormed the keep at dusk."
    assert entry.author_id == user.id
    assert entry.campaign_id == campaign.id
    assert entry.id is not None


async def test_create_entry_no_body(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-cr-nobody", email="svc-chr-cr-nobody@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrc0002")
    entry = await chronicle_service.create_entry(
        db,
        campaign_id=campaign.id,
        slug="quiet-session",
        title="Quiet Session",
        occurred_at=datetime(2024, 1, 1, tzinfo=UTC),
        body=None,
        author_id=user.id,
    )
    assert entry.body is None


async def test_create_entry_slug_conflict_raises(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-cr-conflict", email="svc-chr-cr-conflict@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrc0003")
    await chronicle_service.create_entry(
        db,
        campaign_id=campaign.id,
        slug="session-one",
        title="Session One",
        occurred_at=datetime(2024, 1, 1, tzinfo=UTC),
        body=None,
        author_id=user.id,
    )
    try:
        await chronicle_service.create_entry(
            db,
            campaign_id=campaign.id,
            slug="session-one",
            title="Another Session One",
            occurred_at=datetime(2024, 1, 2, tzinfo=UTC),
            body=None,
            author_id=user.id,
        )
        raise AssertionError("Expected EntrySlugConflictError")
    except EntrySlugConflictError:
        pass


async def test_create_entry_same_slug_different_campaigns_ok(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-cr-xcamp", email="svc-chr-cr-xcamp@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="chrca001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="chrcb001")
    await chronicle_service.create_entry(
        db,
        campaign_id=campaign_a.id,
        slug="session-one",
        title="Session One",
        occurred_at=datetime(2024, 1, 1, tzinfo=UTC),
        body=None,
        author_id=user.id,
    )
    entry = await chronicle_service.create_entry(
        db,
        campaign_id=campaign_b.id,
        slug="session-one",
        title="Session One",
        occurred_at=datetime(2024, 1, 1, tzinfo=UTC),
        body=None,
        author_id=user.id,
    )
    assert entry.slug == "session-one"


# --- get_entry_by_slug ---


async def test_get_entry_by_slug_found(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-gbs-ok", email="svc-chr-gbs-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrs0001")
    await make_chronicle_entry(db, campaign_id=campaign.id, slug="lantern-lit")
    result = await chronicle_service.get_entry_by_slug(db, campaign.id, "lantern-lit", MemberRole.GM)
    assert result is not None
    assert result.slug == "lantern-lit"


async def test_get_entry_by_slug_not_found(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-gbs-404", email="svc-chr-gbs-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrs0002")
    result = await chronicle_service.get_entry_by_slug(db, campaign.id, "nonexistent", MemberRole.GM)
    assert result is None


async def test_get_entry_by_slug_wrong_campaign_returns_none(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-gbs-iso", email="svc-chr-gbs-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="chrsa001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="chrsb001")
    await make_chronicle_entry(db, campaign_id=campaign_b.id, slug="lantern-lit")
    result = await chronicle_service.get_entry_by_slug(db, campaign_a.id, "lantern-lit", MemberRole.GM)
    assert result is None


async def test_get_entry_by_slug_eager_loads_author(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-eager", email="svc-chr-eager@test.com", display_name="Cato")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chre0001")
    entry = await make_chronicle_entry(db, campaign_id=campaign.id, author_id=user.id)
    result = await chronicle_service.get_entry_by_slug(db, campaign.id, entry.slug, MemberRole.GM)
    assert result is not None
    assert result.author is not None
    assert result.author.display_name == "Cato"


async def test_get_entry_by_slug_author_null_after_user_deleted(db: AsyncSession) -> None:
    owner = await make_user(
        db, supertokens_user_id="svc-chr-author-del-owner", email="svc-chr-author-del-owner@test.com"
    )
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="chra0001")
    author = await make_user(db, supertokens_user_id="svc-chr-author-del", email="svc-chr-author-del@test.com")
    entry = await chronicle_service.create_entry(
        db,
        campaign_id=campaign.id,
        slug="session-one",
        title="Session One",
        occurred_at=datetime(2024, 1, 15, 19, tzinfo=UTC),
        body=None,
        author_id=author.id,
    )
    await db.delete(author)
    await db.flush()
    result = await chronicle_service.get_entry_by_slug(db, campaign.id, entry.slug, MemberRole.GM)
    assert result is not None
    assert result.author_id is None
    assert result.author is None


# --- visibility ---


async def test_list_entries_excludes_restricted_for_player(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-vis-list", email="svc-chr-vis-list@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrw0001")
    visible = await make_chronicle_entry(db, campaign_id=campaign.id, slug="visible")
    await make_chronicle_entry(db, campaign_id=campaign.id, slug="secret", restricted=True)
    result = await chronicle_service.list_entries(db, campaign.id, MemberRole.PLAYER)
    assert [entry.id for entry in result] == [visible.id]


async def test_list_entries_includes_restricted_for_gm(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-vis-list-gm", email="svc-chr-vis-list-gm@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrw0002")
    secret = await make_chronicle_entry(db, campaign_id=campaign.id, slug="secret", restricted=True)
    result = await chronicle_service.list_entries(db, campaign.id, MemberRole.GM)
    assert secret.id in [entry.id for entry in result]


async def test_get_entry_by_slug_restricted_returns_none_for_player(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-vis-get", email="svc-chr-vis-get@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrw0003")
    await make_chronicle_entry(db, campaign_id=campaign.id, slug="secret", restricted=True)
    result = await chronicle_service.get_entry_by_slug(db, campaign.id, "secret", MemberRole.PLAYER)
    assert result is None


async def test_get_entry_by_slug_restricted_returns_value_for_gm(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-vis-get-gm", email="svc-chr-vis-get-gm@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrw0004")
    await make_chronicle_entry(db, campaign_id=campaign.id, slug="secret", restricted=True)
    result = await chronicle_service.get_entry_by_slug(db, campaign.id, "secret", MemberRole.GM)
    assert result is not None


async def test_create_entry_restricted_defaults_false(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-vis-cr-default", email="svc-chr-vis-cr-default@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrw0005")
    entry = await chronicle_service.create_entry(
        db,
        campaign_id=campaign.id,
        slug="session-one",
        title="Session One",
        occurred_at=datetime(2024, 1, 1, tzinfo=UTC),
        body=None,
        author_id=user.id,
    )
    assert entry.restricted is False


async def test_create_entry_restricted_true_persists(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-vis-cr-true", email="svc-chr-vis-cr-true@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrw0006")
    entry = await chronicle_service.create_entry(
        db,
        campaign_id=campaign.id,
        slug="session-one",
        title="Session One",
        occurred_at=datetime(2024, 1, 1, tzinfo=UTC),
        body=None,
        author_id=user.id,
        restricted=True,
    )
    assert entry.restricted is True


async def test_update_entry_restricted_toggles(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-vis-upd", email="svc-chr-vis-upd@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrw0007")
    entry = await make_chronicle_entry(db, campaign_id=campaign.id, restricted=False)
    updated = await chronicle_service.update_entry(db, entry, restricted=True)
    assert updated.restricted is True


# --- update_entry ---


async def test_update_entry_title(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-upd-title", email="svc-chr-upd-title@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chru0001")
    entry = await make_chronicle_entry(db, campaign_id=campaign.id, title="Old Title")
    updated = await chronicle_service.update_entry(db, entry, title="New Title")
    assert updated.title == "New Title"


async def test_update_entry_occurred_at(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-upd-occurred", email="svc-chr-upd-occurred@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chru0002")
    entry = await make_chronicle_entry(db, campaign_id=campaign.id, occurred_at=datetime(2024, 1, 1, tzinfo=UTC))
    new_occurred_at = datetime(2024, 3, 1, tzinfo=UTC)
    updated = await chronicle_service.update_entry(db, entry, occurred_at=new_occurred_at)
    assert updated.occurred_at == new_occurred_at


async def test_update_entry_body(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-upd-body", email="svc-chr-upd-body@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chru0003")
    entry = await make_chronicle_entry(db, campaign_id=campaign.id, body="Old body")
    updated = await chronicle_service.update_entry(db, entry, body="New body")
    assert updated.body == "New body"


async def test_update_entry_missing_fields_unchanged(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-upd-miss", email="svc-chr-upd-miss@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chru0004")
    entry = await make_chronicle_entry(db, campaign_id=campaign.id, title="Keep Me", body="Also keep")
    updated = await chronicle_service.update_entry(db, entry, body="Changed")
    assert updated.title == "Keep Me"
    assert updated.body == "Changed"


# --- delete_entry ---


async def test_delete_entry_removes_record(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-del-ok", email="svc-chr-del-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrd0001")
    entry = await make_chronicle_entry(db, campaign_id=campaign.id)
    entry_slug = entry.slug
    await chronicle_service.delete_entry(db, entry)
    result = await chronicle_service.get_entry_by_slug(db, campaign.id, entry_slug, MemberRole.GM)
    assert result is None
