import uuid
from datetime import UTC, datetime
from unittest.mock import ANY

from fastapi import FastAPI, HTTPException
from httpx import AsyncClient
from pydantic_core import MISSING
from pytest_mock import MockerFixture

from api.auth import get_current_user
from api.models import Campaign, CampaignMember, MemberRole, User
from api.routers.campaigns.dependencies import require_campaign_member
from api.services.chronicle import EntrySlugConflictError
from tests.helpers import build_campaign, build_chronicle_entry, build_member, build_user


def _allow_member(inner_app: FastAPI, campaign: Campaign, *, role: MemberRole = MemberRole.GM) -> None:
    inner_app.dependency_overrides[require_campaign_member] = lambda: build_member(campaign_id=campaign.id, role=role)


def _forbid_member(inner_app: FastAPI) -> None:
    def _raise() -> CampaignMember:
        raise HTTPException(status_code=403, detail="Forbidden")

    inner_app.dependency_overrides[require_campaign_member] = _raise


def _authenticate(inner_app: FastAPI, user: User) -> None:
    inner_app.dependency_overrides[get_current_user] = lambda: user


# The `Z`-suffixed timestamp used in request bodies below, parsed to the aware
# datetime Pydantic hands to the service layer — used for exact (non-ANY) assertions.
_OCCURRED_AT = datetime(2024, 1, 15, 19, 0, 0, tzinfo=UTC)


# --- List ---
#
# Ordering (`list_entries` sorts by `occurred_at.desc()`) is not re-tested here:
# a mocked router test can only prove the mock returns what it was told to
# return. That guarantee is covered by the sociable test in
# tests/services/test_chronicle.py.


async def test_list_chronicle_entries_returns_200(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    entry = build_chronicle_entry(campaign_id=campaign.id, slug="session-one", title="Session One")
    _allow_member(inner_app, campaign)
    mock_list = mocker.patch("api.services.chronicle.list_entries", return_value=[entry])

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Session One"
    assert data[0]["slug"] == "session-one"
    assert "author" not in data[0]
    mock_list.assert_awaited_once_with(ANY, campaign.id, MemberRole.GM)


async def test_list_chronicle_entries_delegates_member_role_for_player(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_list = mocker.patch("api.services.chronicle.list_entries", return_value=[])

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries")

    assert response.status_code == 200
    mock_list.assert_awaited_once_with(ANY, campaign.id, MemberRole.PLAYER)


async def test_list_chronicle_entries_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_list = mocker.patch("api.services.chronicle.list_entries")

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries")

    assert response.status_code == 403
    mock_list.assert_not_called()


# --- Create ---


async def test_create_chronicle_entry_returns_201(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    entry = build_chronicle_entry(
        campaign_id=campaign.id,
        slug="the-fall-of-blackspire",
        title="The Fall of Blackspire",
        body="The party stormed the keep at dusk.",
    )
    user = build_user()
    _allow_member(inner_app, campaign)
    _authenticate(inner_app, user)
    mock_create = mocker.patch("api.services.chronicle.create_entry", return_value=entry)

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
    mock_create.assert_awaited_once_with(
        ANY,
        campaign_id=campaign.id,
        slug="the-fall-of-blackspire",
        title="The Fall of Blackspire",
        occurred_at=_OCCURRED_AT,
        body="The party stormed the keep at dusk.",
        author_id=user.id,
        restricted=False,
        tags=[],
    )


async def test_create_chronicle_entry_sets_author_to_current_user(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    user = build_user(display_name="Bram")
    entry = build_chronicle_entry(campaign_id=campaign.id, slug="session-one", title="Session One")
    _allow_member(inner_app, campaign)
    _authenticate(inner_app, user)
    mock_create = mocker.patch("api.services.chronicle.create_entry", return_value=entry)

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={"slug": "session-one", "title": "Session One", "occurred_at": "2024-01-15T19:00:00Z"},
    )

    assert response.status_code == 201
    mock_create.assert_awaited_once_with(
        ANY,
        campaign_id=campaign.id,
        slug="session-one",
        title="Session One",
        occurred_at=_OCCURRED_AT,
        body=None,
        author_id=user.id,
        restricted=False,
        tags=[],
    )


async def test_create_chronicle_entry_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    _authenticate(inner_app, build_user())
    mock_create = mocker.patch("api.services.chronicle.create_entry")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={"slug": "session-one", "title": "Session One", "occurred_at": "2024-01-15T19:00:00Z"},
    )

    assert response.status_code == 403
    mock_create.assert_not_called()


async def test_create_chronicle_entry_empty_title_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    _authenticate(inner_app, build_user())
    mock_create = mocker.patch("api.services.chronicle.create_entry")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={"slug": "session-one", "title": "  ", "occurred_at": "2024-01-15T19:00:00Z"},
    )

    assert response.status_code == 422
    mock_create.assert_not_called()


async def test_create_chronicle_entry_invalid_slug_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    _authenticate(inner_app, build_user())
    mock_create = mocker.patch("api.services.chronicle.create_entry")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={"slug": "Session One!", "title": "Session One", "occurred_at": "2024-01-15T19:00:00Z"},
    )

    assert response.status_code == 422
    mock_create.assert_not_called()


async def test_create_chronicle_entry_naive_occurred_at_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    _authenticate(inner_app, build_user())
    mock_create = mocker.patch("api.services.chronicle.create_entry")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={"slug": "session-one", "title": "Session One", "occurred_at": "2024-01-15T19:00:00"},
    )

    assert response.status_code == 422
    mock_create.assert_not_called()


async def test_create_chronicle_entry_reserved_slug_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    _authenticate(inner_app, build_user())
    mock_create = mocker.patch("api.services.chronicle.create_entry")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={"slug": "new", "title": "New Entry", "occurred_at": "2024-01-15T19:00:00Z"},
    )

    assert response.status_code == 422
    mock_create.assert_not_called()


async def test_create_chronicle_entry_slug_conflict_returns_409(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    user = build_user()
    _allow_member(inner_app, campaign)
    _authenticate(inner_app, user)
    mock_create = mocker.patch("api.services.chronicle.create_entry", side_effect=EntrySlugConflictError())

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={"slug": "session-one", "title": "Another Session One", "occurred_at": "2024-01-15T19:00:00Z"},
    )

    assert response.status_code == 409
    mock_create.assert_awaited_once_with(
        ANY,
        campaign_id=campaign.id,
        slug="session-one",
        title="Another Session One",
        occurred_at=_OCCURRED_AT,
        body=None,
        author_id=user.id,
        restricted=False,
        tags=[],
    )


async def test_create_chronicle_entry_player_member_can_create(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    user = build_user()
    entry = build_chronicle_entry(campaign_id=campaign.id, slug="session-one", title="Session One")
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    _authenticate(inner_app, user)
    mock_create = mocker.patch("api.services.chronicle.create_entry", return_value=entry)

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={"slug": "session-one", "title": "Session One", "occurred_at": "2024-01-15T19:00:00Z"},
    )

    assert response.status_code == 201
    mock_create.assert_awaited_once_with(
        ANY,
        campaign_id=campaign.id,
        slug="session-one",
        title="Session One",
        occurred_at=_OCCURRED_AT,
        body=None,
        author_id=user.id,
        restricted=False,
        tags=[],
    )


async def test_create_chronicle_entry_restricted_defaults_false(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    user = build_user()
    entry = build_chronicle_entry(campaign_id=campaign.id, slug="session-one", restricted=False)
    _allow_member(inner_app, campaign)
    _authenticate(inner_app, user)
    mock_create = mocker.patch("api.services.chronicle.create_entry", return_value=entry)

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={"slug": "session-one", "title": "Session One", "occurred_at": "2024-01-15T19:00:00Z"},
    )

    assert response.status_code == 201
    assert response.json()["restricted"] is False
    mock_create.assert_awaited_once_with(
        ANY,
        campaign_id=campaign.id,
        slug="session-one",
        title="Session One",
        occurred_at=_OCCURRED_AT,
        body=None,
        author_id=user.id,
        restricted=False,
        tags=[],
    )


async def test_create_chronicle_entry_gm_can_set_restricted_true(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    user = build_user()
    entry = build_chronicle_entry(campaign_id=campaign.id, slug="session-one", restricted=True)
    _allow_member(inner_app, campaign)
    _authenticate(inner_app, user)
    mock_create = mocker.patch("api.services.chronicle.create_entry", return_value=entry)

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={
            "slug": "session-one",
            "title": "Session One",
            "occurred_at": "2024-01-15T19:00:00Z",
            "restricted": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["restricted"] is True
    mock_create.assert_awaited_once_with(
        ANY,
        campaign_id=campaign.id,
        slug="session-one",
        title="Session One",
        occurred_at=_OCCURRED_AT,
        body=None,
        author_id=user.id,
        restricted=True,
        tags=[],
    )


async def test_create_chronicle_entry_player_cannot_set_restricted_true(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    _authenticate(inner_app, build_user())
    mock_create = mocker.patch("api.services.chronicle.create_entry")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries",
        json={
            "slug": "session-one",
            "title": "Session One",
            "occurred_at": "2024-01-15T19:00:00Z",
            "restricted": True,
        },
    )

    assert response.status_code == 403
    mock_create.assert_not_called()


# --- Get ---


async def test_get_chronicle_entry_returns_200(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    entry = build_chronicle_entry(campaign_id=campaign.id, slug="session-one", title="Session One")
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug", return_value=entry)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/session-one")

    assert response.status_code == 200
    assert response.json()["title"] == "Session One"
    mock_get.assert_awaited_once_with(ANY, campaign.id, "session-one", MemberRole.GM)


async def test_get_chronicle_entry_delegates_member_role_for_player(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    entry = build_chronicle_entry(campaign_id=campaign.id, slug="session-one", title="Session One")
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug", return_value=entry)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/session-one")

    assert response.status_code == 200
    mock_get.assert_awaited_once_with(ANY, campaign.id, "session-one", MemberRole.PLAYER)


async def test_get_chronicle_entry_includes_author(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    author = build_user(display_name="Aria")
    entry = build_chronicle_entry(campaign_id=campaign.id, author_id=author.id, author=author)
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug", return_value=entry)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/{entry.slug}")

    assert response.status_code == 200
    assert response.json()["author"] == {"id": str(author.id), "display_name": "Aria"}
    mock_get.assert_awaited_once_with(ANY, campaign.id, entry.slug, MemberRole.GM)


async def test_get_chronicle_entry_author_null_when_unset(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    entry = build_chronicle_entry(campaign_id=campaign.id, author_id=None, author=None)
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug", return_value=entry)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/{entry.slug}")

    assert response.status_code == 200
    assert response.json()["author"] is None
    mock_get.assert_awaited_once_with(ANY, campaign.id, entry.slug, MemberRole.GM)


async def test_get_chronicle_entry_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug")

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/session-one")

    assert response.status_code == 403
    mock_get.assert_not_called()


async def test_get_chronicle_entry_returns_404_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug", return_value=None)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/nonexistent-entry")

    assert response.status_code == 404
    mock_get.assert_awaited_once_with(ANY, campaign.id, "nonexistent-entry", MemberRole.GM)


# --- Patch ---


async def test_patch_chronicle_entry_returns_200(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    entry = build_chronicle_entry(campaign_id=campaign.id, slug="old-entry", title="Old")
    updated = build_chronicle_entry(campaign_id=campaign.id, slug="old-entry", title="New")
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug", return_value=entry)
    mock_update = mocker.patch("api.services.chronicle.update_entry", return_value=updated)

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/old-entry",
        json={"title": "New"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "New"
    mock_get.assert_awaited_once_with(ANY, campaign.id, "old-entry", MemberRole.GM, for_update=True)
    mock_update.assert_awaited_once_with(
        ANY, entry, title="New", occurred_at=MISSING, body=MISSING, restricted=MISSING, tags=MISSING
    )


async def test_patch_chronicle_entry_ignores_slug_and_author_id(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    entry = build_chronicle_entry(campaign_id=campaign.id, slug="original-slug")
    updated = build_chronicle_entry(campaign_id=campaign.id, slug="original-slug", title="Updated Title")
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug", return_value=entry)
    mock_update = mocker.patch("api.services.chronicle.update_entry", return_value=updated)

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/original-slug",
        json={"slug": "new-slug", "author_id": str(uuid.uuid4()), "title": "Updated Title"},
    )

    assert response.status_code == 200
    assert response.json()["slug"] == "original-slug"
    assert response.json()["title"] == "Updated Title"
    mock_get.assert_awaited_once_with(ANY, campaign.id, "original-slug", MemberRole.GM, for_update=True)
    mock_update.assert_awaited_once_with(
        ANY, entry, title="Updated Title", occurred_at=MISSING, body=MISSING, restricted=MISSING, tags=MISSING
    )


async def test_patch_chronicle_entry_naive_occurred_at_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    entry = build_chronicle_entry(campaign_id=campaign.id, slug="old-entry")
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.chronicle.get_entry_by_slug", return_value=entry)
    mock_update = mocker.patch("api.services.chronicle.update_entry")

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/old-entry",
        json={"occurred_at": "2024-01-15T19:00:00"},
    )

    assert response.status_code == 422
    mock_update.assert_not_called()


async def test_patch_chronicle_entry_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug")
    mock_update = mocker.patch("api.services.chronicle.update_entry")

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/session-one",
        json={"title": "New"},
    )

    assert response.status_code == 403
    mock_get.assert_not_called()
    mock_update.assert_not_called()


async def test_patch_chronicle_entry_returns_404_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug", return_value=None)
    mock_update = mocker.patch("api.services.chronicle.update_entry")

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/nonexistent-entry",
        json={"title": "New"},
    )

    assert response.status_code == 404
    mock_get.assert_awaited_once_with(ANY, campaign.id, "nonexistent-entry", MemberRole.GM, for_update=True)
    mock_update.assert_not_called()


async def test_patch_chronicle_entry_player_cannot_set_restricted_true(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug")
    mock_update = mocker.patch("api.services.chronicle.update_entry")

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/session-one",
        json={"restricted": True},
    )

    assert response.status_code == 403
    mock_get.assert_not_called()
    mock_update.assert_not_called()


async def test_patch_chronicle_entry_gm_can_set_restricted_true(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    entry = build_chronicle_entry(campaign_id=campaign.id, slug="session-one", restricted=False)
    updated = build_chronicle_entry(campaign_id=campaign.id, slug="session-one", restricted=True)
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug", return_value=entry)
    mock_update = mocker.patch("api.services.chronicle.update_entry", return_value=updated)

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/session-one",
        json={"restricted": True},
    )

    assert response.status_code == 200
    assert response.json()["restricted"] is True
    mock_get.assert_awaited_once_with(ANY, campaign.id, "session-one", MemberRole.GM, for_update=True)
    mock_update.assert_awaited_once_with(
        ANY, entry, title=MISSING, occurred_at=MISSING, body=MISSING, restricted=True, tags=MISSING
    )


async def test_patch_chronicle_entry_player_can_update_non_restricted_fields(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    entry = build_chronicle_entry(campaign_id=campaign.id, slug="session-one", title="Old")
    updated = build_chronicle_entry(campaign_id=campaign.id, slug="session-one", title="New")
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug", return_value=entry)
    mock_update = mocker.patch("api.services.chronicle.update_entry", return_value=updated)

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/session-one",
        json={"title": "New"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "New"
    mock_get.assert_awaited_once_with(ANY, campaign.id, "session-one", MemberRole.PLAYER, for_update=True)
    mock_update.assert_awaited_once_with(
        ANY, entry, title="New", occurred_at=MISSING, body=MISSING, restricted=MISSING, tags=MISSING
    )


# --- Delete ---


async def test_delete_chronicle_entry_returns_204(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    entry = build_chronicle_entry(campaign_id=campaign.id)
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug", return_value=entry)
    mock_delete = mocker.patch("api.services.chronicle.delete_entry")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/{entry.slug}")

    assert response.status_code == 204
    mock_get.assert_awaited_once_with(ANY, campaign.id, entry.slug, MemberRole.GM, for_update=True)
    mock_delete.assert_awaited_once_with(ANY, entry)


async def test_delete_chronicle_entry_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug")
    mock_delete = mocker.patch("api.services.chronicle.delete_entry")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/session-one")

    assert response.status_code == 403
    mock_get.assert_not_called()
    mock_delete.assert_not_called()


async def test_delete_chronicle_entry_returns_404_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug", return_value=None)
    mock_delete = mocker.patch("api.services.chronicle.delete_entry")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/nonexistent-entry")

    assert response.status_code == 404
    mock_get.assert_awaited_once_with(ANY, campaign.id, "nonexistent-entry", MemberRole.GM, for_update=True)
    mock_delete.assert_not_called()


async def test_delete_chronicle_entry_player_member_can_delete(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    entry = build_chronicle_entry(campaign_id=campaign.id)
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_get = mocker.patch("api.services.chronicle.get_entry_by_slug", return_value=entry)
    mock_delete = mocker.patch("api.services.chronicle.delete_entry")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/chronicle/entries/{entry.slug}")

    assert response.status_code == 204
    mock_get.assert_awaited_once_with(ANY, campaign.id, entry.slug, MemberRole.PLAYER, for_update=True)
    mock_delete.assert_awaited_once_with(ANY, entry)
