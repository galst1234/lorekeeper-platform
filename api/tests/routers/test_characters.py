from unittest.mock import ANY

import pytest
from fastapi import FastAPI, HTTPException
from httpx import AsyncClient
from pydantic_core import MISSING
from pytest_mock import MockerFixture

from api.models import Campaign, CampaignMember, CharacterType, MemberRole
from api.routers.campaigns.dependencies import require_campaign_member
from api.services.characters import CharacterSlugConflictError
from api.storage import ImageStorage, get_image_storage
from tests.helpers import build_campaign, build_character, build_member


def _allow_member(inner_app: FastAPI, campaign: Campaign, *, role: MemberRole = MemberRole.GM) -> None:
    inner_app.dependency_overrides[require_campaign_member] = lambda: build_member(campaign_id=campaign.id, role=role)


def _forbid_member(inner_app: FastAPI) -> None:
    def _raise() -> CampaignMember:
        raise HTTPException(status_code=403, detail="Forbidden")

    inner_app.dependency_overrides[require_campaign_member] = _raise


# --- List ---


async def test_list_characters_returns_200(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria", name="Aria")
    _allow_member(inner_app, campaign)
    mock_list = mocker.patch("api.services.characters.list_characters", return_value=[character])

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Aria"
    assert data[0]["slug"] == "aria"
    assert data[0]["character_type"] == "pc"
    mock_list.assert_awaited_once_with(ANY, campaign.id, MemberRole.GM, None)


async def test_list_characters_delegates_member_role_for_player(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_list = mocker.patch("api.services.characters.list_characters", return_value=[])

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters")

    assert response.status_code == 200
    mock_list.assert_awaited_once_with(ANY, campaign.id, MemberRole.PLAYER, None)


async def test_list_characters_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_list = mocker.patch("api.services.characters.list_characters")

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters")

    assert response.status_code == 403
    mock_list.assert_not_called()


# --- Create ---


async def test_create_character_returns_201(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria", name="Aria", description=None)
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.characters.create_character", return_value=character)

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "pc"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "aria"
    assert data["name"] == "Aria"
    assert data["character_type"] == "pc"
    assert data["description"] is None
    mock_create.assert_awaited_once_with(
        ANY,
        campaign_id=campaign.id,
        slug="aria",
        name="Aria",
        character_type=CharacterType.PC,
        description=None,
        restricted=False,
        tags=[],
    )


async def test_create_character_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_create = mocker.patch("api.services.characters.create_character")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "pc"},
    )

    assert response.status_code == 403
    mock_create.assert_not_called()


async def test_create_character_empty_name_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.characters.create_character")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "  ", "character_type": "pc"},
    )

    assert response.status_code == 422
    mock_create.assert_not_called()


async def test_create_character_invalid_type_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.characters.create_character")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "villain"},
    )

    assert response.status_code == 422
    mock_create.assert_not_called()


async def test_create_character_invalid_slug_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.characters.create_character")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "Aria Stormwind", "name": "Aria", "character_type": "pc"},
    )

    assert response.status_code == 422
    mock_create.assert_not_called()


async def test_create_character_reserved_slug_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.characters.create_character")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "new", "name": "New Character", "character_type": "npc"},
    )

    assert response.status_code == 422
    mock_create.assert_not_called()


async def test_create_character_slug_conflict_returns_409(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.characters.create_character", side_effect=CharacterSlugConflictError())

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "gandalf", "name": "Gandalf the White", "character_type": "npc"},
    )

    assert response.status_code == 409
    mock_create.assert_awaited_once_with(
        ANY,
        campaign_id=campaign.id,
        slug="gandalf",
        name="Gandalf the White",
        character_type=CharacterType.NPC,
        description=None,
        restricted=False,
        tags=[],
    )


async def test_create_character_player_member_can_create(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria", name="Aria")
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_create = mocker.patch("api.services.characters.create_character", return_value=character)

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "pc"},
    )

    assert response.status_code == 201
    mock_create.assert_awaited_once_with(
        ANY,
        campaign_id=campaign.id,
        slug="aria",
        name="Aria",
        character_type=CharacterType.PC,
        description=None,
        restricted=False,
        tags=[],
    )


async def test_create_character_restricted_defaults_false(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria", name="Aria", restricted=False)
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.characters.create_character", return_value=character)

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "pc"},
    )

    assert response.status_code == 201
    assert response.json()["restricted"] is False
    mock_create.assert_awaited_once_with(
        ANY,
        campaign_id=campaign.id,
        slug="aria",
        name="Aria",
        character_type=CharacterType.PC,
        description=None,
        restricted=False,
        tags=[],
    )


async def test_create_character_gm_can_set_restricted_true(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria", name="Aria", restricted=True)
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.characters.create_character", return_value=character)

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "pc", "restricted": True},
    )

    assert response.status_code == 201
    assert response.json()["restricted"] is True
    mock_create.assert_awaited_once_with(
        ANY,
        campaign_id=campaign.id,
        slug="aria",
        name="Aria",
        character_type=CharacterType.PC,
        description=None,
        restricted=True,
        tags=[],
    )


async def test_create_character_player_cannot_set_restricted_true(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_create = mocker.patch("api.services.characters.create_character")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "pc", "restricted": True},
    )

    assert response.status_code == 403
    mock_create.assert_not_called()


# --- Get ---


async def test_get_character_returns_200(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria", name="Aria")
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.characters.get_character_by_slug", return_value=character)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters/aria")

    assert response.status_code == 200
    assert response.json()["name"] == "Aria"
    assert response.json()["slug"] == "aria"
    mock_get.assert_awaited_once_with(ANY, campaign.id, "aria", MemberRole.GM)


async def test_get_character_delegates_member_role_for_player(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria", name="Aria")
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_get = mocker.patch("api.services.characters.get_character_by_slug", return_value=character)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters/aria")

    assert response.status_code == 200
    mock_get.assert_awaited_once_with(ANY, campaign.id, "aria", MemberRole.PLAYER)


async def test_get_character_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_get = mocker.patch("api.services.characters.get_character_by_slug")

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters/aria")

    assert response.status_code == 403
    mock_get.assert_not_called()


async def test_get_character_returns_404_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.characters.get_character_by_slug", return_value=None)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters/nonexistent-character")

    assert response.status_code == 404
    mock_get.assert_awaited_once_with(ANY, campaign.id, "nonexistent-character", MemberRole.GM)


# --- Patch ---


async def test_patch_character_returns_200(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="old-char", name="Old")
    updated = build_character(campaign_id=campaign.id, slug="old-char", name="New")
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.characters.get_character_by_slug", return_value=character)
    mock_update = mocker.patch("api.services.characters.update_character", return_value=updated)

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/characters/old-char",
        json={"name": "New"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "New"
    mock_get.assert_awaited_once_with(ANY, campaign.id, "old-char", MemberRole.GM)
    mock_update.assert_awaited_once_with(
        ANY, character, name="New", character_type=MISSING, description=MISSING, restricted=MISSING, tags=MISSING
    )


async def test_patch_character_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_get = mocker.patch("api.services.characters.get_character_by_slug")
    mock_update = mocker.patch("api.services.characters.update_character")

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/characters/aria",
        json={"name": "New"},
    )

    assert response.status_code == 403
    mock_get.assert_not_called()
    mock_update.assert_not_called()


async def test_patch_character_returns_404_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.characters.get_character_by_slug", return_value=None)
    mock_update = mocker.patch("api.services.characters.update_character")

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/characters/nonexistent-character",
        json={"name": "New"},
    )

    assert response.status_code == 404
    mock_get.assert_awaited_once_with(ANY, campaign.id, "nonexistent-character", MemberRole.GM)
    mock_update.assert_not_called()


async def test_patch_character_player_cannot_set_restricted_true(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_get = mocker.patch("api.services.characters.get_character_by_slug")
    mock_update = mocker.patch("api.services.characters.update_character")

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/characters/aria",
        json={"restricted": True},
    )

    assert response.status_code == 403
    mock_get.assert_not_called()
    mock_update.assert_not_called()


async def test_patch_character_gm_can_set_restricted_true(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria", name="Aria", restricted=False)
    updated = build_character(campaign_id=campaign.id, slug="aria", name="Aria", restricted=True)
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.characters.get_character_by_slug", return_value=character)
    mock_update = mocker.patch("api.services.characters.update_character", return_value=updated)

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/characters/aria",
        json={"restricted": True},
    )

    assert response.status_code == 200
    assert response.json()["restricted"] is True
    mock_update.assert_awaited_once_with(
        ANY, character, name=MISSING, character_type=MISSING, description=MISSING, restricted=True, tags=MISSING
    )


async def test_patch_character_player_can_update_non_restricted_fields(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria", name="Aria")
    updated = build_character(campaign_id=campaign.id, slug="aria", name="Aria Renamed")
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_get = mocker.patch("api.services.characters.get_character_by_slug", return_value=character)
    mock_update = mocker.patch("api.services.characters.update_character", return_value=updated)

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/characters/aria",
        json={"name": "Aria Renamed"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Aria Renamed"
    mock_get.assert_awaited_once_with(ANY, campaign.id, "aria", MemberRole.PLAYER)
    mock_update.assert_awaited_once_with(
        ANY,
        character,
        name="Aria Renamed",
        character_type=MISSING,
        description=MISSING,
        restricted=MISSING,
        tags=MISSING,
    )


# --- Delete ---


async def test_delete_character_returns_204(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria")
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.characters.get_character_by_slug", return_value=character)
    mock_delete = mocker.patch("api.services.characters.delete_character")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/aria")

    assert response.status_code == 204
    mock_get.assert_awaited_once_with(ANY, campaign.id, "aria", MemberRole.GM)
    mock_delete.assert_awaited_once_with(ANY, character, ANY)


async def test_delete_character_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_get = mocker.patch("api.services.characters.get_character_by_slug")
    mock_delete = mocker.patch("api.services.characters.delete_character")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/aria")

    assert response.status_code == 403
    mock_get.assert_not_called()
    mock_delete.assert_not_called()


async def test_delete_character_returns_404_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.characters.get_character_by_slug", return_value=None)
    mock_delete = mocker.patch("api.services.characters.delete_character")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/nonexistent-character")

    assert response.status_code == 404
    mock_get.assert_awaited_once_with(ANY, campaign.id, "nonexistent-character", MemberRole.GM)
    mock_delete.assert_not_called()


async def test_delete_character_player_member_can_delete(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria")
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_get = mocker.patch("api.services.characters.get_character_by_slug", return_value=character)
    mock_delete = mocker.patch("api.services.characters.delete_character")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/aria")

    assert response.status_code == 204
    mock_get.assert_awaited_once_with(ANY, campaign.id, "aria", MemberRole.PLAYER)
    mock_delete.assert_awaited_once_with(ANY, character, ANY)


# --- Image (solitary — see tests/CLAUDE.md) ---


@pytest.fixture
def image_client(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> tuple[AsyncClient, FastAPI, ImageStorage]:
    ac, inner_app = campaigns_client
    image_storage = mocker.create_autospec(ImageStorage, instance=True)
    inner_app.dependency_overrides[get_image_storage] = lambda: image_storage
    return ac, inner_app, image_storage


async def test_upload_character_image_returns_200_with_image_url(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria", name="Aria")
    updated = build_character(campaign_id=campaign.id, slug="aria", name="Aria", image_key="new-key.jpg")
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.characters.get_character_by_slug", return_value=character)
    mock_set = mocker.patch("api.services.characters.set_character_image", return_value=updated)
    image_storage.save.return_value = "new-key.jpg"
    image_storage.url_for.return_value = "/media/new-key.jpg"

    response = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}/image",
        files={"file": ("portrait.jpg", b"fake-jpeg-bytes", "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json()["image_url"] == "/media/new-key.jpg"
    image_storage.save.assert_awaited_once_with(b"fake-jpeg-bytes", "image/jpeg")
    mock_set.assert_awaited_once_with(ANY, character, "new-key.jpg", image_storage)


async def test_upload_character_image_rejects_invalid_content_type(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria", name="Aria")
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.characters.get_character_by_slug", return_value=character)
    mock_set = mocker.patch("api.services.characters.set_character_image")

    response = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}/image",
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400
    image_storage.save.assert_not_called()
    mock_set.assert_not_called()


async def test_upload_character_image_rejects_oversized_file(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria", name="Aria")
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.characters.get_character_by_slug", return_value=character)
    mock_set = mocker.patch("api.services.characters.set_character_image")
    oversized_content = b"x" * (5 * 1024 * 1024 + 1)

    response = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}/image",
        files={"file": ("portrait.jpg", oversized_content, "image/jpeg")},
    )

    assert response.status_code == 400
    image_storage.save.assert_not_called()
    mock_set.assert_not_called()


async def test_upload_character_image_replaces_existing_and_changes_url(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria", name="Aria", image_key="old-key.jpg")
    first_updated = build_character(campaign_id=campaign.id, slug="aria", name="Aria", image_key="first-key.jpg")
    second_updated = build_character(campaign_id=campaign.id, slug="aria", name="Aria", image_key="second-key.png")
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.characters.get_character_by_slug", return_value=character)
    mocker.patch("api.services.characters.set_character_image", side_effect=[first_updated, second_updated])
    image_storage.save.side_effect = ["first-key.jpg", "second-key.png"]
    image_storage.url_for.side_effect = lambda key: f"/media/{key}"

    first = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}/image",
        files={"file": ("first.jpg", b"first-bytes", "image/jpeg")},
    )
    second = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}/image",
        files={"file": ("second.png", b"second-bytes", "image/png")},
    )

    assert second.status_code == 200
    assert second.json()["image_url"] != first.json()["image_url"]


async def test_upload_character_image_returns_403_for_non_member(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_get = mocker.patch("api.services.characters.get_character_by_slug")
    mock_set = mocker.patch("api.services.characters.set_character_image")

    response = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/characters/aria/image",
        files={"file": ("portrait.jpg", b"bytes", "image/jpeg")},
    )

    assert response.status_code == 403
    mock_get.assert_not_called()
    mock_set.assert_not_called()
    image_storage.save.assert_not_called()


async def test_upload_character_image_returns_404_not_found(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.characters.get_character_by_slug", return_value=None)
    mock_set = mocker.patch("api.services.characters.set_character_image")

    response = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/characters/nonexistent-character/image",
        files={"file": ("portrait.jpg", b"bytes", "image/jpeg")},
    )

    assert response.status_code == 404
    image_storage.save.assert_not_called()
    mock_set.assert_not_called()


# --- Delete image (solitary — see tests/CLAUDE.md) ---


async def test_delete_character_image_returns_204_and_clears_url(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria", name="Aria", image_key="existing-key.jpg")
    cleared = build_character(campaign_id=campaign.id, slug="aria", name="Aria", image_key=None)
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.characters.get_character_by_slug", return_value=character)
    mock_clear = mocker.patch("api.services.characters.clear_character_image", return_value=cleared)

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}/image")

    assert response.status_code == 204
    mock_clear.assert_awaited_once_with(ANY, character, image_storage)


async def test_delete_character_image_with_no_existing_image_returns_204(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria", name="Aria")
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.characters.get_character_by_slug", return_value=character)
    mock_clear = mocker.patch("api.services.characters.clear_character_image", return_value=character)

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}/image")

    assert response.status_code == 204
    mock_clear.assert_awaited_once_with(ANY, character, image_storage)


async def test_delete_character_image_returns_403_for_non_member(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_get = mocker.patch("api.services.characters.get_character_by_slug")
    mock_clear = mocker.patch("api.services.characters.clear_character_image")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/aria/image")

    assert response.status_code == 403
    mock_get.assert_not_called()
    mock_clear.assert_not_called()
    assert image_storage.save.await_count == 0


async def test_delete_character_also_removes_image_file(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    # File deletion itself is proven by the service-layer test (tests/services/test_characters.py);
    # this only proves the route delegates the right character/image_storage to the function that owns it.
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    character = build_character(campaign_id=campaign.id, slug="aria", name="Aria", image_key="existing-key.jpg")
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.characters.get_character_by_slug", return_value=character)
    mock_delete = mocker.patch("api.services.characters.delete_character")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}")

    assert response.status_code == 204
    mock_delete.assert_awaited_once_with(ANY, character, image_storage)
