from collections.abc import Callable
from datetime import UTC, datetime

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers import make_campaign, make_chronicle_entry, make_member, make_user

# --- List ---


async def test_list_chronicle_entries_returns_200(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-list-200", email="rt-chr-list-200@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcl0001")
    await make_chronicle_entry(db, campaign_id=campaign.id, slug="session-one", title="Session One")
    ac = campaigns_authenticated_client("rt-chr-list-200")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["title"] == "Session One"
    assert data[0]["slug"] == "session-one"


async def test_list_chronicle_entries_excludes_author(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-list-noauthor", email="rt-chr-list-noauthor@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcl0002")
    await make_chronicle_entry(db, campaign_id=campaign.id, author_id=user.id)
    ac = campaigns_authenticated_client("rt-chr-list-noauthor")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries")
    assert response.status_code == 200
    assert "author" not in response.json()[0]


async def test_list_chronicle_entries_orders_by_occurred_at(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-list-ord", email="rt-chr-list-ord@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcl0003")
    recent_session = await make_chronicle_entry(
        db,
        campaign_id=campaign.id,
        slug="session-two",
        title="Session Two",
        occurred_at=datetime(2024, 2, 1, tzinfo=UTC),
    )
    backfilled_older_session = await make_chronicle_entry(
        db,
        campaign_id=campaign.id,
        slug="session-one",
        title="Session One",
        occurred_at=datetime(2024, 1, 1, tzinfo=UTC),
    )
    ac = campaigns_authenticated_client("rt-chr-list-ord")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries")
    data = response.json()
    assert data[0]["id"] == str(recent_session.id)
    assert data[1]["id"] == str(backfilled_older_session.id)


async def test_list_chronicle_entries_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-list-own", email="rt-chr-list-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcl0004")
    await make_user(db, supertokens_user_id="rt-chr-list-403", email="rt-chr-list-403@test.com")
    ac = campaigns_authenticated_client("rt-chr-list-403")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries")
    assert response.status_code == 403


# --- Create ---


async def test_create_chronicle_entry_returns_201(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-cr-201", email="rt-chr-cr-201@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0001")
    ac = campaigns_authenticated_client("rt-chr-cr-201")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={
            "slug": "the-fall-of-blackspire",
            "title": "The Fall of Blackspire",
            "occurred_at": "2024-01-15T19:00:00Z",
            "body": "The party stormed the keep at dusk.",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "the-fall-of-blackspire"
    assert data["title"] == "The Fall of Blackspire"
    assert data["body"] == "The party stormed the keep at dusk."
    assert "author" not in data


async def test_create_chronicle_entry_sets_author_to_current_user(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(
        db, supertokens_user_id="rt-chr-cr-author", email="rt-chr-cr-author@test.com", display_name="Bram"
    )
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0002")
    ac = campaigns_authenticated_client("rt-chr-cr-author")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={"slug": "session-one", "title": "Session One", "occurred_at": "2024-01-15T19:00:00Z"},
    )
    assert response.status_code == 201
    entry_slug = response.json()["slug"]
    detail = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/{entry_slug}")
    assert detail.json()["author"] == {"id": str(user.id), "display_name": "Bram"}


async def test_create_chronicle_entry_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-cr-own", email="rt-chr-cr-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcc0003")
    await make_user(db, supertokens_user_id="rt-chr-cr-403", email="rt-chr-cr-403@test.com")
    ac = campaigns_authenticated_client("rt-chr-cr-403")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={"slug": "session-one", "title": "Session One", "occurred_at": "2024-01-15T19:00:00Z"},
    )
    assert response.status_code == 403


async def test_create_chronicle_entry_empty_title_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-cr-notitle", email="rt-chr-cr-notitle@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0004")
    ac = campaigns_authenticated_client("rt-chr-cr-notitle")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={"slug": "session-one", "title": "  ", "occurred_at": "2024-01-15T19:00:00Z"},
    )
    assert response.status_code == 422


async def test_create_chronicle_entry_invalid_slug_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-cr-badslug", email="rt-chr-cr-badslug@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0005")
    ac = campaigns_authenticated_client("rt-chr-cr-badslug")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={"slug": "Session One!", "title": "Session One", "occurred_at": "2024-01-15T19:00:00Z"},
    )
    assert response.status_code == 422


async def test_create_chronicle_entry_slug_conflict_returns_409(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-cr-conflict", email="rt-chr-cr-conflict@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0006")
    await make_chronicle_entry(db, campaign_id=campaign.id, slug="session-one")
    ac = campaigns_authenticated_client("rt-chr-cr-conflict")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={"slug": "session-one", "title": "Another Session One", "occurred_at": "2024-01-15T19:00:00Z"},
    )
    assert response.status_code == 409


async def test_create_chronicle_entry_player_member_can_create(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-cr-plown", email="rt-chr-cr-plown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcc0007")
    player = await make_user(db, supertokens_user_id="rt-chr-cr-player", email="rt-chr-cr-player@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    ac = campaigns_authenticated_client("rt-chr-cr-player")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={"slug": "session-one", "title": "Session One", "occurred_at": "2024-01-15T19:00:00Z"},
    )
    assert response.status_code == 201


# --- Get ---


async def test_get_chronicle_entry_returns_200(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-get-200", email="rt-chr-get-200@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcg0001")
    entry = await make_chronicle_entry(db, campaign_id=campaign.id, slug="session-one", title="Session One")
    ac = campaigns_authenticated_client("rt-chr-get-200")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/{entry.slug}")
    assert response.status_code == 200
    assert response.json()["title"] == "Session One"


async def test_get_chronicle_entry_includes_author(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(
        db, supertokens_user_id="rt-chr-get-author", email="rt-chr-get-author@test.com", display_name="Aria"
    )
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcg0002")
    entry = await make_chronicle_entry(db, campaign_id=campaign.id, author_id=user.id)
    ac = campaigns_authenticated_client("rt-chr-get-author")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/{entry.slug}")
    assert response.json()["author"] == {"id": str(user.id), "display_name": "Aria"}


async def test_get_chronicle_entry_author_null_when_unset(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-get-noauthor", email="rt-chr-get-noauthor@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcg0003")
    entry = await make_chronicle_entry(db, campaign_id=campaign.id, author_id=None)
    ac = campaigns_authenticated_client("rt-chr-get-noauthor")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/{entry.slug}")
    assert response.json()["author"] is None


async def test_get_chronicle_entry_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-get-own", email="rt-chr-get-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcg0004")
    entry = await make_chronicle_entry(db, campaign_id=campaign.id)
    await make_user(db, supertokens_user_id="rt-chr-get-403", email="rt-chr-get-403@test.com")
    ac = campaigns_authenticated_client("rt-chr-get-403")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/{entry.slug}")
    assert response.status_code == 403


async def test_get_chronicle_entry_returns_404_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-get-404", email="rt-chr-get-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcg0005")
    ac = campaigns_authenticated_client("rt-chr-get-404")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/nonexistent-entry")
    assert response.status_code == 404


async def test_get_chronicle_entry_returns_404_for_wrong_campaign(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-get-iso", email="rt-chr-get-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="rtcga001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="rtcgb001")
    entry = await make_chronicle_entry(db, campaign_id=campaign_b.id)
    ac = campaigns_authenticated_client("rt-chr-get-iso")
    response = await ac.get(f"/api/v1/campaigns/{campaign_a.slug}/chronicle/entries/{entry.slug}")
    assert response.status_code == 404


# --- Patch ---


async def test_patch_chronicle_entry_returns_200(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-patch-200", email="rt-chr-patch-200@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcp0001")
    entry = await make_chronicle_entry(db, campaign_id=campaign.id, slug="old-entry", title="Old")
    ac = campaigns_authenticated_client("rt-chr-patch-200")
    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/{entry.slug}",
        json={"title": "New"},
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New"


async def test_patch_chronicle_entry_ignores_slug_and_author_id(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-patch-ignore", email="rt-chr-patch-ignore@test.com")
    other_user = await make_user(db, supertokens_user_id="rt-chr-patch-other", email="rt-chr-patch-other@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcp0002")
    entry = await make_chronicle_entry(db, campaign_id=campaign.id, slug="original-slug", author_id=user.id)
    ac = campaigns_authenticated_client("rt-chr-patch-ignore")
    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/{entry.slug}",
        json={"slug": "new-slug", "author_id": str(other_user.id), "title": "Updated Title"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "original-slug"
    assert data["title"] == "Updated Title"
    detail = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/original-slug")
    assert detail.json()["author"]["id"] == str(user.id)


async def test_patch_chronicle_entry_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-patch-own", email="rt-chr-patch-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcp0003")
    entry = await make_chronicle_entry(db, campaign_id=campaign.id)
    await make_user(db, supertokens_user_id="rt-chr-patch-403", email="rt-chr-patch-403@test.com")
    ac = campaigns_authenticated_client("rt-chr-patch-403")
    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/{entry.slug}",
        json={"title": "New"},
    )
    assert response.status_code == 403


async def test_patch_chronicle_entry_returns_404_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-patch-404", email="rt-chr-patch-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcp0004")
    ac = campaigns_authenticated_client("rt-chr-patch-404")
    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/nonexistent-entry",
        json={"title": "New"},
    )
    assert response.status_code == 404


# --- Delete ---


async def test_delete_chronicle_entry_returns_204(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-del-204", email="rt-chr-del-204@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcd0001")
    entry = await make_chronicle_entry(db, campaign_id=campaign.id)
    ac = campaigns_authenticated_client("rt-chr-del-204")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/{entry.slug}")
    assert response.status_code == 204


async def test_delete_chronicle_entry_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-del-own", email="rt-chr-del-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcd0002")
    entry = await make_chronicle_entry(db, campaign_id=campaign.id)
    await make_user(db, supertokens_user_id="rt-chr-del-403", email="rt-chr-del-403@test.com")
    ac = campaigns_authenticated_client("rt-chr-del-403")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/{entry.slug}")
    assert response.status_code == 403


async def test_delete_chronicle_entry_returns_404_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-del-404", email="rt-chr-del-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcd0003")
    ac = campaigns_authenticated_client("rt-chr-del-404")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/nonexistent-entry")
    assert response.status_code == 404


async def test_delete_chronicle_entry_player_member_can_delete(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-del-plown", email="rt-chr-del-plown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcd0004")
    player = await make_user(db, supertokens_user_id="rt-chr-del-player", email="rt-chr-del-player@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    entry = await make_chronicle_entry(db, campaign_id=campaign.id)
    ac = campaigns_authenticated_client("rt-chr-del-player")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/{entry.slug}")
    assert response.status_code == 204
