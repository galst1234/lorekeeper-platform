from unittest.mock import ANY

import pytest
from fastapi import FastAPI, HTTPException
from httpx import AsyncClient
from pydantic_core import MISSING
from pytest_mock import MockerFixture

from api.models import Campaign, CampaignMember, MemberRole
from api.routers.campaigns.dependencies import require_campaign_member
from api.services.items import ItemSlugConflictError
from api.storage import ImageStorage, get_image_storage
from tests.helpers import build_campaign, build_item, build_member


def _allow_member(inner_app: FastAPI, campaign: Campaign, *, role: MemberRole = MemberRole.GM) -> None:
    inner_app.dependency_overrides[require_campaign_member] = lambda: build_member(campaign_id=campaign.id, role=role)


def _forbid_member(inner_app: FastAPI) -> None:
    def _raise() -> CampaignMember:
        raise HTTPException(status_code=403, detail="Forbidden")

    inner_app.dependency_overrides[require_campaign_member] = _raise


# --- List ---


async def test_list_items_returns_200(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword", name="Sword")
    _allow_member(inner_app, campaign)
    mock_list = mocker.patch("api.services.items.list_items", return_value=[item])

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/items")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Sword"
    assert data[0]["slug"] == "sword"
    mock_list.assert_awaited_once_with(ANY, campaign.id, MemberRole.GM)


async def test_list_items_delegates_member_role_for_player(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_list = mocker.patch("api.services.items.list_items", return_value=[])

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/items")

    assert response.status_code == 200
    mock_list.assert_awaited_once_with(ANY, campaign.id, MemberRole.PLAYER)


async def test_list_items_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_list = mocker.patch("api.services.items.list_items")

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/items")

    assert response.status_code == 403
    mock_list.assert_not_called()


# --- Create ---


async def test_create_item_returns_201(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword", name="Sword", description=None)
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.items.create_item", return_value=item)

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "sword", "name": "Sword"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "sword"
    assert data["name"] == "Sword"
    assert data["description"] is None
    mock_create.assert_awaited_once_with(
        ANY, campaign_id=campaign.id, slug="sword", name="Sword", description=None, restricted=False, tags=[]
    )


async def test_create_item_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_create = mocker.patch("api.services.items.create_item")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "sword", "name": "Sword"},
    )

    assert response.status_code == 403
    mock_create.assert_not_called()


async def test_create_item_empty_name_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.items.create_item")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "sword", "name": "  "},
    )

    assert response.status_code == 422
    mock_create.assert_not_called()


async def test_create_item_invalid_slug_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.items.create_item")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "Sword Of Doom", "name": "Sword"},
    )

    assert response.status_code == 422
    mock_create.assert_not_called()


async def test_create_item_reserved_slug_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.items.create_item")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "new", "name": "New Item"},
    )

    assert response.status_code == 422
    mock_create.assert_not_called()


async def test_create_item_slug_conflict_returns_409(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.items.create_item", side_effect=ItemSlugConflictError())

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "sword", "name": "Another Sword"},
    )

    assert response.status_code == 409
    mock_create.assert_awaited_once_with(
        ANY, campaign_id=campaign.id, slug="sword", name="Another Sword", description=None, restricted=False, tags=[]
    )


async def test_create_item_player_member_can_create(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword", name="Sword")
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_create = mocker.patch("api.services.items.create_item", return_value=item)

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "sword", "name": "Sword"},
    )

    assert response.status_code == 201
    mock_create.assert_awaited_once_with(
        ANY, campaign_id=campaign.id, slug="sword", name="Sword", description=None, restricted=False, tags=[]
    )


async def test_create_item_restricted_defaults_false(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword", name="Sword", restricted=False)
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.items.create_item", return_value=item)

    response = await ac.post(f"/api/v1/campaigns/{campaign.slug}/items", json={"slug": "sword", "name": "Sword"})

    assert response.status_code == 201
    assert response.json()["restricted"] is False
    mock_create.assert_awaited_once_with(
        ANY, campaign_id=campaign.id, slug="sword", name="Sword", description=None, restricted=False, tags=[]
    )


async def test_create_item_gm_can_set_restricted_true(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword", name="Sword", restricted=True)
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.items.create_item", return_value=item)

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "sword", "name": "Sword", "restricted": True},
    )

    assert response.status_code == 201
    assert response.json()["restricted"] is True
    mock_create.assert_awaited_once_with(
        ANY, campaign_id=campaign.id, slug="sword", name="Sword", description=None, restricted=True, tags=[]
    )


async def test_create_item_player_cannot_set_restricted_true(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_create = mocker.patch("api.services.items.create_item")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/items",
        json={"slug": "sword", "name": "Sword", "restricted": True},
    )

    assert response.status_code == 403
    mock_create.assert_not_called()


# --- Get ---


async def test_get_item_returns_200(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword", name="Sword")
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.items.get_item_by_slug", return_value=item)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/items/sword")

    assert response.status_code == 200
    assert response.json()["name"] == "Sword"
    assert response.json()["slug"] == "sword"
    mock_get.assert_awaited_once_with(ANY, campaign.id, "sword", MemberRole.GM)


async def test_get_item_delegates_member_role_for_player(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword", name="Sword")
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_get = mocker.patch("api.services.items.get_item_by_slug", return_value=item)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/items/sword")

    assert response.status_code == 200
    mock_get.assert_awaited_once_with(ANY, campaign.id, "sword", MemberRole.PLAYER)


async def test_get_item_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_get = mocker.patch("api.services.items.get_item_by_slug")

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/items/sword")

    assert response.status_code == 403
    mock_get.assert_not_called()


async def test_get_item_returns_404_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.items.get_item_by_slug", return_value=None)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/items/nonexistent-item")

    assert response.status_code == 404
    mock_get.assert_awaited_once_with(ANY, campaign.id, "nonexistent-item", MemberRole.GM)


# --- Patch ---


async def test_patch_item_returns_200(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="old-item", name="Old")
    updated = build_item(campaign_id=campaign.id, slug="old-item", name="New")
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.items.get_item_by_slug", return_value=item)
    mock_update = mocker.patch("api.services.items.update_item", return_value=updated)

    response = await ac.patch(f"/api/v1/campaigns/{campaign.slug}/items/old-item", json={"name": "New"})

    assert response.status_code == 200
    assert response.json()["name"] == "New"
    mock_get.assert_awaited_once_with(ANY, campaign.id, "old-item", MemberRole.GM, for_update=True)
    mock_update.assert_awaited_once_with(ANY, item, name="New", description=MISSING, restricted=MISSING, tags=MISSING)


async def test_patch_item_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_get = mocker.patch("api.services.items.get_item_by_slug")
    mock_update = mocker.patch("api.services.items.update_item")

    response = await ac.patch(f"/api/v1/campaigns/{campaign.slug}/items/sword", json={"name": "New"})

    assert response.status_code == 403
    mock_get.assert_not_called()
    mock_update.assert_not_called()


async def test_patch_item_returns_404_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.items.get_item_by_slug", return_value=None)
    mock_update = mocker.patch("api.services.items.update_item")

    response = await ac.patch(f"/api/v1/campaigns/{campaign.slug}/items/nonexistent-item", json={"name": "New"})

    assert response.status_code == 404
    mock_get.assert_awaited_once_with(ANY, campaign.id, "nonexistent-item", MemberRole.GM, for_update=True)
    mock_update.assert_not_called()


async def test_patch_item_player_cannot_set_restricted_true(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_get = mocker.patch("api.services.items.get_item_by_slug")
    mock_update = mocker.patch("api.services.items.update_item")

    response = await ac.patch(f"/api/v1/campaigns/{campaign.slug}/items/sword", json={"restricted": True})

    assert response.status_code == 403
    mock_get.assert_not_called()
    mock_update.assert_not_called()


async def test_patch_item_gm_can_set_restricted_true(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword", name="Sword", restricted=False)
    updated = build_item(campaign_id=campaign.id, slug="sword", name="Sword", restricted=True)
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.items.get_item_by_slug", return_value=item)
    mock_update = mocker.patch("api.services.items.update_item", return_value=updated)

    response = await ac.patch(f"/api/v1/campaigns/{campaign.slug}/items/sword", json={"restricted": True})

    assert response.status_code == 200
    assert response.json()["restricted"] is True
    mock_get.assert_awaited_once_with(ANY, campaign.id, "sword", MemberRole.GM, for_update=True)
    mock_update.assert_awaited_once_with(ANY, item, name=MISSING, description=MISSING, restricted=True, tags=MISSING)


async def test_patch_item_player_can_update_non_restricted_fields(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword", name="Sword")
    updated = build_item(campaign_id=campaign.id, slug="sword", name="Sword Renamed")
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_get = mocker.patch("api.services.items.get_item_by_slug", return_value=item)
    mock_update = mocker.patch("api.services.items.update_item", return_value=updated)

    response = await ac.patch(f"/api/v1/campaigns/{campaign.slug}/items/sword", json={"name": "Sword Renamed"})

    assert response.status_code == 200
    assert response.json()["name"] == "Sword Renamed"
    mock_get.assert_awaited_once_with(ANY, campaign.id, "sword", MemberRole.PLAYER, for_update=True)
    mock_update.assert_awaited_once_with(
        ANY, item, name="Sword Renamed", description=MISSING, restricted=MISSING, tags=MISSING
    )


# --- Delete ---


async def test_delete_item_returns_204(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword")
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.items.get_item_by_slug", return_value=item)
    mock_delete = mocker.patch("api.services.items.delete_item")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/sword")

    assert response.status_code == 204
    mock_get.assert_awaited_once_with(ANY, campaign.id, "sword", MemberRole.GM, for_update=True)
    mock_delete.assert_awaited_once_with(ANY, item, ANY)


async def test_delete_item_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_get = mocker.patch("api.services.items.get_item_by_slug")
    mock_delete = mocker.patch("api.services.items.delete_item")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/sword")

    assert response.status_code == 403
    mock_get.assert_not_called()
    mock_delete.assert_not_called()


async def test_delete_item_returns_404_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.items.get_item_by_slug", return_value=None)
    mock_delete = mocker.patch("api.services.items.delete_item")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/nonexistent-item")

    assert response.status_code == 404
    mock_get.assert_awaited_once_with(ANY, campaign.id, "nonexistent-item", MemberRole.GM, for_update=True)
    mock_delete.assert_not_called()


async def test_delete_item_player_member_can_delete(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sword")
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_get = mocker.patch("api.services.items.get_item_by_slug", return_value=item)
    mock_delete = mocker.patch("api.services.items.delete_item")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/sword")

    assert response.status_code == 204
    mock_get.assert_awaited_once_with(ANY, campaign.id, "sword", MemberRole.PLAYER, for_update=True)
    mock_delete.assert_awaited_once_with(ANY, item, ANY)


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
