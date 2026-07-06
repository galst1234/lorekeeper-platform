from collections.abc import Callable

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers import make_campaign, make_item, make_member, make_user

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


# --- Image ---


async def test_upload_item_image_returns_200_with_image_url(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-item-img-200", email="rt-item-img-200@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtii0001")
    item = await make_item(db, campaign_id=campaign.id, slug="sword", name="Sword")
    ac = campaigns_authenticated_client("rt-item-img-200")
    response = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image",
        files={"file": ("sword.jpg", b"fake-jpeg-bytes", "image/jpeg")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["image_url"] is not None
    assert data["image_url"].startswith("/media/")


async def test_upload_item_image_rejects_invalid_content_type(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-item-img-badtype", email="rt-item-img-badtype@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtii0002")
    item = await make_item(db, campaign_id=campaign.id, slug="sword", name="Sword")
    ac = campaigns_authenticated_client("rt-item-img-badtype")
    response = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image",
        files={"file": ("notes.txt", b"not an image", "text/plain")},
    )
    assert response.status_code == 400


async def test_upload_item_image_rejects_oversized_file(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-item-img-big", email="rt-item-img-big@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtii0003")
    item = await make_item(db, campaign_id=campaign.id, slug="sword", name="Sword")
    ac = campaigns_authenticated_client("rt-item-img-big")
    oversized_content = b"x" * (5 * 1024 * 1024 + 1)
    response = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image",
        files={"file": ("sword.jpg", oversized_content, "image/jpeg")},
    )
    assert response.status_code == 400


async def test_upload_item_image_replaces_existing_and_changes_url(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-item-img-replace", email="rt-item-img-replace@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtii0004")
    item = await make_item(db, campaign_id=campaign.id, slug="sword", name="Sword")
    ac = campaigns_authenticated_client("rt-item-img-replace")
    first = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image",
        files={"file": ("first.jpg", b"first-bytes", "image/jpeg")},
    )
    first_url = first.json()["image_url"]
    second = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image",
        files={"file": ("second.png", b"second-bytes", "image/png")},
    )
    assert second.status_code == 200
    assert second.json()["image_url"] != first_url


async def test_upload_item_image_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-item-img-own", email="rt-item-img-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtii0005")
    item = await make_item(db, campaign_id=campaign.id)
    await make_user(db, supertokens_user_id="rt-item-img-403", email="rt-item-img-403@test.com")
    ac = campaigns_authenticated_client("rt-item-img-403")
    response = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image",
        files={"file": ("sword.jpg", b"bytes", "image/jpeg")},
    )
    assert response.status_code == 403


async def test_upload_item_image_returns_404_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-item-img-404", email="rt-item-img-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtii0006")
    ac = campaigns_authenticated_client("rt-item-img-404")
    response = await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/items/nonexistent-item/image",
        files={"file": ("sword.jpg", b"bytes", "image/jpeg")},
    )
    assert response.status_code == 404


# --- Delete image ---


async def test_delete_item_image_returns_204_and_clears_url(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-item-imgdel-204", email="rt-item-imgdel-204@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtiid001")
    item = await make_item(db, campaign_id=campaign.id, slug="sword", name="Sword")
    ac = campaigns_authenticated_client("rt-item-imgdel-204")
    await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image",
        files={"file": ("sword.jpg", b"bytes", "image/jpeg")},
    )
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image")
    assert response.status_code == 204
    get_response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}")
    assert get_response.json()["image_url"] is None


async def test_delete_item_image_with_no_existing_image_returns_204(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-item-imgdel-noop", email="rt-item-imgdel-noop@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtiid002")
    item = await make_item(db, campaign_id=campaign.id, slug="sword", name="Sword")
    ac = campaigns_authenticated_client("rt-item-imgdel-noop")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image")
    assert response.status_code == 204


async def test_delete_item_image_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-item-imgdel-own", email="rt-item-imgdel-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtiid003")
    item = await make_item(db, campaign_id=campaign.id)
    await make_user(db, supertokens_user_id="rt-item-imgdel-403", email="rt-item-imgdel-403@test.com")
    ac = campaigns_authenticated_client("rt-item-imgdel-403")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image")
    assert response.status_code == 403


async def test_delete_item_also_removes_image_file(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-item-del-img", email="rt-item-del-img@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtidi001")
    item = await make_item(db, campaign_id=campaign.id, slug="sword", name="Sword")
    ac = campaigns_authenticated_client("rt-item-del-img")
    await ac.put(
        f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}/image",
        files={"file": ("sword.jpg", b"bytes", "image/jpeg")},
    )
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/items/{item.slug}")
    assert response.status_code == 204
