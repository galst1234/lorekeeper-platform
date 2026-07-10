from collections.abc import Callable
from unittest.mock import ANY

import pytest
from fastapi import FastAPI, HTTPException
from httpx import AsyncClient
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Campaign, CampaignMember
from api.routers.campaigns.dependencies import require_campaign_member
from api.storage import ImageStorage, get_image_storage
from tests.helpers import (
    build_campaign,
    build_character,
    build_member,
    make_campaign,
    make_character,
    make_member,
    make_user,
)

# --- List ---


async def test_list_characters_returns_200(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-list-200", email="rt-chr-list-200@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcl0001")
    await make_character(db, campaign_id=campaign.id, slug="aria", name="Aria")
    ac = campaigns_authenticated_client("rt-chr-list-200")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Aria"
    assert data[0]["slug"] == "aria"
    assert data[0]["character_type"] == "pc"


async def test_list_characters_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-list-own", email="rt-chr-list-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcl0002")
    await make_user(db, supertokens_user_id="rt-chr-list-403", email="rt-chr-list-403@test.com")
    ac = campaigns_authenticated_client("rt-chr-list-403")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters")
    assert response.status_code == 403


# --- Create ---


async def test_create_character_returns_201(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-cr-201", email="rt-chr-cr-201@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0001")
    ac = campaigns_authenticated_client("rt-chr-cr-201")
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


async def test_create_character_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-cr-own", email="rt-chr-cr-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcc0002")
    await make_user(db, supertokens_user_id="rt-chr-cr-403", email="rt-chr-cr-403@test.com")
    ac = campaigns_authenticated_client("rt-chr-cr-403")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "pc"},
    )
    assert response.status_code == 403


async def test_create_character_empty_name_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-cr-noname", email="rt-chr-cr-noname@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0003")
    ac = campaigns_authenticated_client("rt-chr-cr-noname")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "  ", "character_type": "pc"},
    )
    assert response.status_code == 422


async def test_create_character_invalid_type_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-cr-badtype", email="rt-chr-cr-badtype@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0004")
    ac = campaigns_authenticated_client("rt-chr-cr-badtype")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "villain"},
    )
    assert response.status_code == 422


async def test_create_character_invalid_slug_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-cr-badslug", email="rt-chr-cr-badslug@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0005")
    ac = campaigns_authenticated_client("rt-chr-cr-badslug")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "Aria Stormwind", "name": "Aria", "character_type": "pc"},
    )
    assert response.status_code == 422


async def test_create_character_reserved_slug_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-cr-reserved", email="rt-chr-cr-reserved@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0007")
    ac = campaigns_authenticated_client("rt-chr-cr-reserved")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "new", "name": "New Character", "character_type": "npc"},
    )
    assert response.status_code == 422


async def test_create_character_slug_conflict_returns_409(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-cr-conflict", email="rt-chr-cr-conflict@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0006")
    await make_character(db, campaign_id=campaign.id, slug="gandalf")
    ac = campaigns_authenticated_client("rt-chr-cr-conflict")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "gandalf", "name": "Gandalf the White", "character_type": "npc"},
    )
    assert response.status_code == 409


async def test_create_character_player_member_can_create(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-cr-plown", email="rt-chr-cr-plown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcc0007")
    player = await make_user(db, supertokens_user_id="rt-chr-cr-player", email="rt-chr-cr-player@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    ac = campaigns_authenticated_client("rt-chr-cr-player")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "pc"},
    )
    assert response.status_code == 201


# --- Get ---


async def test_get_character_returns_200(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-get-200", email="rt-chr-get-200@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcg0001")
    character = await make_character(db, campaign_id=campaign.id, slug="aria", name="Aria")
    ac = campaigns_authenticated_client("rt-chr-get-200")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}")
    assert response.status_code == 200
    assert response.json()["name"] == "Aria"
    assert response.json()["slug"] == "aria"


async def test_get_character_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-get-own", email="rt-chr-get-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcg0002")
    character = await make_character(db, campaign_id=campaign.id)
    await make_user(db, supertokens_user_id="rt-chr-get-403", email="rt-chr-get-403@test.com")
    ac = campaigns_authenticated_client("rt-chr-get-403")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}")
    assert response.status_code == 403


async def test_get_character_returns_404_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-get-404", email="rt-chr-get-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcg0003")
    ac = campaigns_authenticated_client("rt-chr-get-404")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters/nonexistent-character")
    assert response.status_code == 404


async def test_get_character_returns_404_for_wrong_campaign(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-get-iso", email="rt-chr-get-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="rtcga001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="rtcgb001")
    character = await make_character(db, campaign_id=campaign_b.id)
    ac = campaigns_authenticated_client("rt-chr-get-iso")
    response = await ac.get(f"/api/v1/campaigns/{campaign_a.slug}/characters/{character.slug}")
    assert response.status_code == 404


# --- Patch ---


async def test_patch_character_returns_200(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-patch-200", email="rt-chr-patch-200@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcp0001")
    character = await make_character(db, campaign_id=campaign.id, slug="old-char", name="Old")
    ac = campaigns_authenticated_client("rt-chr-patch-200")
    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}",
        json={"name": "New"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New"


async def test_patch_character_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-patch-own", email="rt-chr-patch-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcp0002")
    character = await make_character(db, campaign_id=campaign.id)
    await make_user(db, supertokens_user_id="rt-chr-patch-403", email="rt-chr-patch-403@test.com")
    ac = campaigns_authenticated_client("rt-chr-patch-403")
    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}",
        json={"name": "New"},
    )
    assert response.status_code == 403


# --- Delete ---


async def test_delete_character_returns_204(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-del-204", email="rt-chr-del-204@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcd0001")
    character = await make_character(db, campaign_id=campaign.id)
    ac = campaigns_authenticated_client("rt-chr-del-204")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}")
    assert response.status_code == 204


async def test_delete_character_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-del-own", email="rt-chr-del-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcd0002")
    character = await make_character(db, campaign_id=campaign.id)
    await make_user(db, supertokens_user_id="rt-chr-del-403", email="rt-chr-del-403@test.com")
    ac = campaigns_authenticated_client("rt-chr-del-403")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}")
    assert response.status_code == 403


async def test_delete_character_returns_404_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-del-404", email="rt-chr-del-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcd0003")
    ac = campaigns_authenticated_client("rt-chr-del-404")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/nonexistent-character")
    assert response.status_code == 404


async def test_delete_character_player_member_can_delete(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-del-plown", email="rt-chr-del-plown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcd0004")
    player = await make_user(db, supertokens_user_id="rt-chr-del-player", email="rt-chr-del-player@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    character = await make_character(db, campaign_id=campaign.id)
    ac = campaigns_authenticated_client("rt-chr-del-player")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}")
    assert response.status_code == 204


# --- Restricted ---


async def test_create_character_restricted_defaults_false(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-res-default", email="rt-chr-res-default@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtrd0001")
    ac = campaigns_authenticated_client("rt-chr-res-default")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "pc"},
    )
    assert response.status_code == 201
    assert response.json()["restricted"] is False


async def test_create_character_gm_can_set_restricted_true(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-res-gm", email="rt-chr-res-gm@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtrg0001")
    ac = campaigns_authenticated_client("rt-chr-res-gm")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "pc", "restricted": True},
    )
    assert response.status_code == 201
    assert response.json()["restricted"] is True


async def test_create_character_player_cannot_set_restricted_true(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-res-plown", email="rt-chr-res-plown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtrp0001")
    player = await make_user(db, supertokens_user_id="rt-chr-res-player", email="rt-chr-res-player@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    ac = campaigns_authenticated_client("rt-chr-res-player")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "pc", "restricted": True},
    )
    assert response.status_code == 403


async def test_patch_character_player_cannot_set_restricted_true(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-res-patchown", email="rt-chr-res-patchown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtrq0001")
    player = await make_user(db, supertokens_user_id="rt-chr-res-patchplayer", email="rt-chr-res-patchplayer@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    character = await make_character(db, campaign_id=campaign.id, slug="aria")
    ac = campaigns_authenticated_client("rt-chr-res-patchplayer")
    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}",
        json={"restricted": True},
    )
    assert response.status_code == 403


async def test_list_characters_excludes_restricted_for_player(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-res-listown", email="rt-chr-res-listown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtrl0001")
    player = await make_user(db, supertokens_user_id="rt-chr-res-listplayer", email="rt-chr-res-listplayer@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    await make_character(db, campaign_id=campaign.id, slug="visible", name="Visible", restricted=False)
    await make_character(db, campaign_id=campaign.id, slug="secret", name="Secret", restricted=True)
    ac = campaigns_authenticated_client("rt-chr-res-listplayer")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters")
    names = [character["name"] for character in response.json()]
    assert names == ["Visible"]


async def test_list_characters_includes_restricted_for_gm(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-res-listgm", email="rt-chr-res-listgm@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtrm0001")
    await make_character(db, campaign_id=campaign.id, slug="secret", name="Secret", restricted=True)
    ac = campaigns_authenticated_client("rt-chr-res-listgm")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters")
    names = [character["name"] for character in response.json()]
    assert names == ["Secret"]


async def test_get_character_returns_404_for_restricted_as_player(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-res-getown", email="rt-chr-res-getown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtrn0001")
    player = await make_user(db, supertokens_user_id="rt-chr-res-getplayer", email="rt-chr-res-getplayer@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    character = await make_character(db, campaign_id=campaign.id, slug="secret", restricted=True)
    ac = campaigns_authenticated_client("rt-chr-res-getplayer")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}")
    assert response.status_code == 404


async def test_patch_character_returns_404_for_restricted_as_player(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-res-patchgetown", email="rt-chr-res-patchgetown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtro0001")
    player = await make_user(
        db, supertokens_user_id="rt-chr-res-patchgetplayer", email="rt-chr-res-patchgetplayer@test.com"
    )
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    character = await make_character(db, campaign_id=campaign.id, slug="secret", restricted=True)
    ac = campaigns_authenticated_client("rt-chr-res-patchgetplayer")
    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}",
        json={"name": "New Name"},
    )
    assert response.status_code == 404


async def test_delete_character_returns_404_for_restricted_as_player(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-res-delgetown", email="rt-chr-res-delgetown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtrs0001")
    player = await make_user(
        db, supertokens_user_id="rt-chr-res-delgetplayer", email="rt-chr-res-delgetplayer@test.com"
    )
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    character = await make_character(db, campaign_id=campaign.id, slug="secret", restricted=True)
    ac = campaigns_authenticated_client("rt-chr-res-delgetplayer")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}")
    assert response.status_code == 404


# --- Image (solitary — see tests/CLAUDE.md) ---


def _allow_member(inner_app: FastAPI, campaign: Campaign) -> None:
    inner_app.dependency_overrides[require_campaign_member] = lambda: build_member(campaign_id=campaign.id)


def _forbid_member(inner_app: FastAPI) -> None:
    def _raise() -> CampaignMember:
        raise HTTPException(status_code=403, detail="Forbidden")

    inner_app.dependency_overrides[require_campaign_member] = _raise


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
