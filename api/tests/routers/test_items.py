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
from tests.helpers import build_campaign, build_item, build_member, make_campaign, make_item, make_member, make_user

# --- List ---


async def test_list_items_returns_200(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-itm-list-200", email="rt-itm-list-200@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtil0001")
    await make_item(db, campaign_id=campaign.id, slug="sword", name="Sword")
    ac = campaigns_authenticated_client("rt-itm-list-200")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/items")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Sword"
    assert data[0]["slug"] == "sword"


async def test_list_items_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-itm-list-own", email="rt-itm-list-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtil0002")
    await make_user(db, supertokens_user_id="rt-itm-list-403", email="rt-itm-list-403@test.com")
    ac = campaigns_authenticated_client("rt-itm-list-403")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/items")
    assert response.status_code == 403


# --- Create ---


async def test_create_item_returns_201(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-itm-cr-201", email="rt-itm-cr-201@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtic0001")
    ac = campaigns_authenticated_client("rt-itm-cr-201")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "sword", "name": "Sword"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "sword"
    assert data["name"] == "Sword"
    assert data["description"] is None


async def test_create_item_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-itm-cr-own", email="rt-itm-cr-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtic0002")
    await make_user(db, supertokens_user_id="rt-itm-cr-403", email="rt-itm-cr-403@test.com")
    ac = campaigns_authenticated_client("rt-itm-cr-403")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "sword", "name": "Sword"},
    )
    assert response.status_code == 403


async def test_create_item_empty_name_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-itm-cr-noname", email="rt-itm-cr-noname@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtic0003")
    ac = campaigns_authenticated_client("rt-itm-cr-noname")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "sword", "name": "  "},
    )
    assert response.status_code == 422


async def test_create_item_invalid_slug_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-itm-cr-badslug", email="rt-itm-cr-badslug@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtic0004")
    ac = campaigns_authenticated_client("rt-itm-cr-badslug")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "Sword Of Doom", "name": "Sword"},
    )
    assert response.status_code == 422


async def test_create_item_reserved_slug_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-itm-cr-reserved", email="rt-itm-cr-reserved@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtic0007")
    ac = campaigns_authenticated_client("rt-itm-cr-reserved")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "new", "name": "New Item"},
    )
    assert response.status_code == 422


async def test_create_item_slug_conflict_returns_409(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-itm-cr-conflict", email="rt-itm-cr-conflict@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtic0005")
    await make_item(db, campaign_id=campaign.id, slug="sword")
    ac = campaigns_authenticated_client("rt-itm-cr-conflict")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "sword", "name": "Another Sword"},
    )
    assert response.status_code == 409


async def test_create_item_player_member_can_create(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-itm-cr-plown", email="rt-itm-cr-plown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtic0006")
    player = await make_user(db, supertokens_user_id="rt-itm-cr-player", email="rt-itm-cr-player@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    ac = campaigns_authenticated_client("rt-itm-cr-player")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "sword", "name": "Sword"},
    )
    assert response.status_code == 201


# --- Get ---


async def test_get_item_returns_200(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-itm-get-200", email="rt-itm-get-200@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtig0001")
    item = await make_item(db, campaign_id=campaign.id, slug="sword", name="Sword")
    ac = campaigns_authenticated_client("rt-itm-get-200")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}")
    assert response.status_code == 200
    assert response.json()["name"] == "Sword"
    assert response.json()["slug"] == "sword"


async def test_get_item_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-itm-get-own", email="rt-itm-get-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtig0002")
    item = await make_item(db, campaign_id=campaign.id)
    await make_user(db, supertokens_user_id="rt-itm-get-403", email="rt-itm-get-403@test.com")
    ac = campaigns_authenticated_client("rt-itm-get-403")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}")
    assert response.status_code == 403


async def test_get_item_returns_404_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-itm-get-404", email="rt-itm-get-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtig0003")
    ac = campaigns_authenticated_client("rt-itm-get-404")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/items/nonexistent-item")
    assert response.status_code == 404


async def test_get_item_returns_404_for_wrong_campaign(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-itm-get-iso", email="rt-itm-get-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="rtiga001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="rtigb001")
    item = await make_item(db, campaign_id=campaign_b.id)
    ac = campaigns_authenticated_client("rt-itm-get-iso")
    response = await ac.get(f"/api/v1/campaigns/{campaign_a.slug}/items/{item.slug}")
    assert response.status_code == 404


# --- Patch ---


async def test_patch_item_returns_200(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-itm-patch-200", email="rt-itm-patch-200@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtip0001")
    item = await make_item(db, campaign_id=campaign.id, slug="old-item", name="Old")
    ac = campaigns_authenticated_client("rt-itm-patch-200")
    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}",
        json={"name": "New"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New"


async def test_patch_item_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-itm-patch-own", email="rt-itm-patch-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtip0002")
    item = await make_item(db, campaign_id=campaign.id)
    await make_user(db, supertokens_user_id="rt-itm-patch-403", email="rt-itm-patch-403@test.com")
    ac = campaigns_authenticated_client("rt-itm-patch-403")
    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}",
        json={"name": "New"},
    )
    assert response.status_code == 403


# --- Delete ---


async def test_delete_item_returns_204(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-itm-del-204", email="rt-itm-del-204@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtid0001")
    item = await make_item(db, campaign_id=campaign.id)
    ac = campaigns_authenticated_client("rt-itm-del-204")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}")
    assert response.status_code == 204


async def test_delete_item_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-itm-del-own", email="rt-itm-del-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtid0002")
    item = await make_item(db, campaign_id=campaign.id)
    await make_user(db, supertokens_user_id="rt-itm-del-403", email="rt-itm-del-403@test.com")
    ac = campaigns_authenticated_client("rt-itm-del-403")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}")
    assert response.status_code == 403


async def test_delete_item_returns_404_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-itm-del-404", email="rt-itm-del-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtid0003")
    ac = campaigns_authenticated_client("rt-itm-del-404")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/nonexistent-item")
    assert response.status_code == 404


async def test_delete_item_player_member_can_delete(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-itm-del-plown", email="rt-itm-del-plown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtid0004")
    player = await make_user(db, supertokens_user_id="rt-itm-del-player", email="rt-itm-del-player@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    item = await make_item(db, campaign_id=campaign.id)
    ac = campaigns_authenticated_client("rt-itm-del-player")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}")
    assert response.status_code == 204


# --- Restricted ---


async def test_create_item_restricted_defaults_false(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-itm-res-default", email="rt-itm-res-default@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtird001")
    ac = campaigns_authenticated_client("rt-itm-res-default")
    response = await ac.post(f"/api/v1/campaigns/{campaign.slug}/items", json={"slug": "sword", "name": "Sword"})
    assert response.status_code == 201
    assert response.json()["restricted"] is False


async def test_create_item_gm_can_set_restricted_true(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-itm-res-gm", email="rt-itm-res-gm@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtirg001")
    ac = campaigns_authenticated_client("rt-itm-res-gm")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "sword", "name": "Sword", "restricted": True},
    )
    assert response.status_code == 201
    assert response.json()["restricted"] is True


async def test_create_item_player_cannot_set_restricted_true(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-itm-res-plown", email="rt-itm-res-plown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtirp001")
    player = await make_user(db, supertokens_user_id="rt-itm-res-player", email="rt-itm-res-player@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    ac = campaigns_authenticated_client("rt-itm-res-player")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "sword", "name": "Sword", "restricted": True},
    )
    assert response.status_code == 403


async def test_patch_item_player_cannot_set_restricted_true(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-itm-res-patchown", email="rt-itm-res-patchown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtirq001")
    player = await make_user(db, supertokens_user_id="rt-itm-res-patchplayer", email="rt-itm-res-patchplayer@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    item = await make_item(db, campaign_id=campaign.id, slug="sword")
    ac = campaigns_authenticated_client("rt-itm-res-patchplayer")
    response = await ac.patch(f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}", json={"restricted": True})
    assert response.status_code == 403


async def test_list_items_excludes_restricted_for_player(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-itm-res-listown", email="rt-itm-res-listown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtirl001")
    player = await make_user(db, supertokens_user_id="rt-itm-res-listplayer", email="rt-itm-res-listplayer@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    await make_item(db, campaign_id=campaign.id, slug="visible", name="Visible", restricted=False)
    await make_item(db, campaign_id=campaign.id, slug="secret", name="Secret", restricted=True)
    ac = campaigns_authenticated_client("rt-itm-res-listplayer")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/items")
    names = [item["name"] for item in response.json()]
    assert names == ["Visible"]


async def test_list_items_includes_restricted_for_gm(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-itm-res-listgm", email="rt-itm-res-listgm@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtirm001")
    await make_item(db, campaign_id=campaign.id, slug="secret", name="Secret", restricted=True)
    ac = campaigns_authenticated_client("rt-itm-res-listgm")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/items")
    names = [item["name"] for item in response.json()]
    assert names == ["Secret"]


async def test_get_item_returns_404_for_restricted_as_player(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-itm-res-getown", email="rt-itm-res-getown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtirn001")
    player = await make_user(db, supertokens_user_id="rt-itm-res-getplayer", email="rt-itm-res-getplayer@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    item = await make_item(db, campaign_id=campaign.id, slug="secret", restricted=True)
    ac = campaigns_authenticated_client("rt-itm-res-getplayer")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}")
    assert response.status_code == 404


async def test_patch_item_returns_404_for_restricted_as_player(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-itm-res-patchgetown", email="rt-itm-res-patchgetown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtiro001")
    player = await make_user(
        db, supertokens_user_id="rt-itm-res-patchgetplayer", email="rt-itm-res-patchgetplayer@test.com"
    )
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    item = await make_item(db, campaign_id=campaign.id, slug="secret", restricted=True)
    ac = campaigns_authenticated_client("rt-itm-res-patchgetplayer")
    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}",
        json={"name": "New Name"},
    )
    assert response.status_code == 404


async def test_delete_item_returns_404_for_restricted_as_player(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-itm-res-delgetown", email="rt-itm-res-delgetown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtirs001")
    player = await make_user(
        db, supertokens_user_id="rt-itm-res-delgetplayer", email="rt-itm-res-delgetplayer@test.com"
    )
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    item = await make_item(db, campaign_id=campaign.id, slug="secret", restricted=True)
    ac = campaigns_authenticated_client("rt-itm-res-delgetplayer")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}")
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


async def test_upload_item_image_returns_200_with_image_url(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword", name="Sword")
    updated = build_item(campaign_id=campaign.id, slug="sword", name="Sword", image_key="new-key.jpg")
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.items.get_item_by_slug", return_value=item)
    mock_set = mocker.patch("api.services.items.set_item_image", return_value=updated)
    image_storage.save.return_value = "new-key.jpg"
    image_storage.url_for.return_value = "/media/new-key.jpg"

    response = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image",
        files={"file": ("sword.jpg", b"fake-jpeg-bytes", "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json()["image_url"] == "/media/new-key.jpg"
    image_storage.save.assert_awaited_once_with(b"fake-jpeg-bytes", "image/jpeg")
    mock_set.assert_awaited_once_with(ANY, item, "new-key.jpg", image_storage)


async def test_upload_item_image_rejects_invalid_content_type(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword", name="Sword")
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.items.get_item_by_slug", return_value=item)
    mock_set = mocker.patch("api.services.items.set_item_image")

    response = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image",
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )

    assert response.status_code == 400
    image_storage.save.assert_not_called()
    mock_set.assert_not_called()


async def test_upload_item_image_rejects_oversized_file(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword", name="Sword")
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.items.get_item_by_slug", return_value=item)
    mock_set = mocker.patch("api.services.items.set_item_image")
    oversized_content = b"x" * (5 * 1024 * 1024 + 1)

    response = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image",
        files={"file": ("sword.jpg", oversized_content, "image/jpeg")},
    )

    assert response.status_code == 400
    image_storage.save.assert_not_called()
    mock_set.assert_not_called()


async def test_upload_item_image_replaces_existing_and_changes_url(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword", name="Sword", image_key="old-key.jpg")
    first_updated = build_item(campaign_id=campaign.id, slug="sword", name="Sword", image_key="first-key.jpg")
    second_updated = build_item(campaign_id=campaign.id, slug="sword", name="Sword", image_key="second-key.png")
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.items.get_item_by_slug", return_value=item)
    mocker.patch("api.services.items.set_item_image", side_effect=[first_updated, second_updated])
    image_storage.save.side_effect = ["first-key.jpg", "second-key.png"]
    image_storage.url_for.side_effect = lambda key: f"/media/{key}"

    first = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image",
        files={"file": ("first.jpg", b"first-bytes", "image/jpeg")},
    )
    second = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image",
        files={"file": ("second.png", b"second-bytes", "image/png")},
    )

    assert second.status_code == 200
    assert second.json()["image_url"] != first.json()["image_url"]


async def test_upload_item_image_returns_403_for_non_member(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_get = mocker.patch("api.services.items.get_item_by_slug")
    mock_set = mocker.patch("api.services.items.set_item_image")

    response = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/items/sword/image",
        files={"file": ("sword.jpg", b"bytes", "image/jpeg")},
    )

    assert response.status_code == 403
    mock_get.assert_not_called()
    mock_set.assert_not_called()
    image_storage.save.assert_not_called()


async def test_upload_item_image_returns_404_not_found(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.items.get_item_by_slug", return_value=None)
    mock_set = mocker.patch("api.services.items.set_item_image")

    response = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/items/nonexistent-item/image",
        files={"file": ("sword.jpg", b"bytes", "image/jpeg")},
    )

    assert response.status_code == 404
    image_storage.save.assert_not_called()
    mock_set.assert_not_called()


# --- Delete image (solitary — see tests/CLAUDE.md) ---


async def test_delete_item_image_returns_204_and_clears_url(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword", name="Sword", image_key="existing-key.jpg")
    cleared = build_item(campaign_id=campaign.id, slug="sword", name="Sword", image_key=None)
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.items.get_item_by_slug", return_value=item)
    mock_clear = mocker.patch("api.services.items.clear_item_image", return_value=cleared)

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image")

    assert response.status_code == 204
    mock_clear.assert_awaited_once_with(ANY, item, image_storage)


async def test_delete_item_image_with_no_existing_image_returns_204(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword", name="Sword")
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.items.get_item_by_slug", return_value=item)
    mock_clear = mocker.patch("api.services.items.clear_item_image", return_value=item)

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image")

    assert response.status_code == 204
    mock_clear.assert_awaited_once_with(ANY, item, image_storage)


async def test_delete_item_image_returns_403_for_non_member(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_get = mocker.patch("api.services.items.get_item_by_slug")
    mock_clear = mocker.patch("api.services.items.clear_item_image")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/sword/image")

    assert response.status_code == 403
    mock_get.assert_not_called()
    mock_clear.assert_not_called()
    assert image_storage.save.await_count == 0


async def test_delete_item_also_removes_image_file(
    image_client: tuple[AsyncClient, FastAPI, ImageStorage],
    mocker: MockerFixture,
) -> None:
    # File deletion itself is proven by the service-layer test (tests/services/test_items.py);
    # this only proves the route delegates the right item/image_storage to the function that owns it.
    ac, inner_app, image_storage = image_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword", name="Sword", image_key="existing-key.jpg")
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.items.get_item_by_slug", return_value=item)
    mock_delete = mocker.patch("api.services.items.delete_item")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}")

    assert response.status_code == 204
    mock_delete.assert_awaited_once_with(ANY, item, image_storage)
