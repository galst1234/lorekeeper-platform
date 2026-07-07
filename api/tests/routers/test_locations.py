from collections.abc import Callable

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers import link_location, make_campaign, make_location, make_member, make_user

# --- List ---


async def test_list_campaign_locations_returns_200(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-loc-list-200", email="rt-loc-list-200@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtll0001")
    location = await make_location(db, owner_id=user.id, slug="tavern", name="Tavern")
    await link_location(db, campaign_id=campaign.id, location_id=location.id)
    ac = campaigns_authenticated_client("rt-loc-list-200")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/locations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Tavern"
    assert data[0]["slug"] == "tavern"
    assert data[0]["is_active"] is True
    assert "added_at" in data[0]
    assert "created_at" in data[0]
    assert "updated_at" in data[0]


async def test_list_campaign_locations_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-loc-list-own", email="rt-loc-list-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtll0002")
    await make_user(db, supertokens_user_id="rt-loc-list-403", email="rt-loc-list-403@test.com")
    ac = campaigns_authenticated_client("rt-loc-list-403")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/locations")
    assert response.status_code == 403


async def test_list_campaign_locations_filters_active_only(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-loc-list-active", email="rt-loc-list-active@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtll0003")
    active_location = await make_location(db, owner_id=user.id, slug="tavern", name="Tavern")
    inactive_location = await make_location(db, owner_id=user.id, slug="dungeon", name="Dungeon")
    await link_location(db, campaign_id=campaign.id, location_id=active_location.id, is_active=True)
    await link_location(db, campaign_id=campaign.id, location_id=inactive_location.id, is_active=False)
    ac = campaigns_authenticated_client("rt-loc-list-active")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/locations", params={"active_only": "true"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["slug"] == "tavern"
    assert data[0]["is_active"] is True


# --- Create ---


async def test_create_campaign_location_returns_201(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-loc-cr-201", email="rt-loc-cr-201@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtlc0001")
    ac = campaigns_authenticated_client("rt-loc-cr-201")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/locations",
        json={"slug": "tavern", "name": "Tavern", "description": "A cozy inn.", "notes": "Session 1", "is_active": True},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "tavern"
    assert data["name"] == "Tavern"
    assert data["description"] == "A cozy inn."
    assert data["notes"] == "Session 1"
    assert data["is_active"] is True
    assert "id" in data
    assert "added_at" in data
    assert "created_at" in data
    assert "updated_at" in data


async def test_create_campaign_location_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-loc-cr-own", email="rt-loc-cr-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtlc0002")
    await make_user(db, supertokens_user_id="rt-loc-cr-403", email="rt-loc-cr-403@test.com")
    ac = campaigns_authenticated_client("rt-loc-cr-403")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/locations",
        json={"slug": "tavern", "name": "Tavern"},
    )
    assert response.status_code == 403


async def test_create_campaign_location_returns_409_on_duplicate_slug(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-loc-cr-dupslug", email="rt-loc-cr-dupslug@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtlc0003")
    await make_location(db, owner_id=user.id, slug="tavern", name="Existing Tavern")
    ac = campaigns_authenticated_client("rt-loc-cr-dupslug")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/locations",
        json={"slug": "tavern", "name": "Another Tavern"},
    )
    assert response.status_code == 409


async def test_create_campaign_location_returns_409_when_already_linked(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-loc-cr-linked", email="rt-loc-cr-linked@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtlc0004")
    location = await make_location(db, owner_id=user.id, slug="tavern", name="Tavern")
    await link_location(db, campaign_id=campaign.id, location_id=location.id)
    ac = campaigns_authenticated_client("rt-loc-cr-linked")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/locations",
        json={"slug": "tavern", "name": "Tavern"},
    )
    assert response.status_code == 409


async def test_create_campaign_location_empty_name_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-loc-cr-noname", email="rt-loc-cr-noname@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtlc0005")
    ac = campaigns_authenticated_client("rt-loc-cr-noname")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/locations",
        json={"slug": "tavern", "name": "  "},
    )
    assert response.status_code == 422


async def test_create_campaign_location_invalid_slug_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-loc-cr-badslug", email="rt-loc-cr-badslug@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtlc0006")
    ac = campaigns_authenticated_client("rt-loc-cr-badslug")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/locations",
        json={"slug": "Tavern Square", "name": "Tavern"},
    )
    assert response.status_code == 422


async def test_create_campaign_location_reserved_slug_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-loc-cr-reserved", email="rt-loc-cr-reserved@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtlc0007")
    ac = campaigns_authenticated_client("rt-loc-cr-reserved")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/locations",
        json={"slug": "new", "name": "New Location"},
    )
    assert response.status_code == 422


async def test_create_campaign_location_player_member_can_create(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-loc-cr-plown", email="rt-loc-cr-plown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtlc0008")
    player = await make_user(db, supertokens_user_id="rt-loc-cr-player", email="rt-loc-cr-player@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    ac = campaigns_authenticated_client("rt-loc-cr-player")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/locations",
        json={"slug": "tavern", "name": "Tavern"},
    )
    assert response.status_code == 201


# --- Get ---


async def test_get_campaign_location_returns_200(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-loc-get-200", email="rt-loc-get-200@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtlg0001")
    location = await make_location(db, owner_id=user.id, slug="tavern", name="Tavern", description="An inn.")
    await link_location(db, campaign_id=campaign.id, location_id=location.id, notes="First stop")
    ac = campaigns_authenticated_client("rt-loc-get-200")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/locations/{location.slug}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Tavern"
    assert data["slug"] == "tavern"
    assert data["description"] == "An inn."
    assert data["notes"] == "First stop"
    assert data["is_active"] is True
    assert "added_at" in data
    assert "created_at" in data
    assert "updated_at" in data


async def test_get_campaign_location_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-loc-get-own", email="rt-loc-get-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtlg0002")
    location = await make_location(db, owner_id=owner.id, slug="tavern")
    await link_location(db, campaign_id=campaign.id, location_id=location.id)
    await make_user(db, supertokens_user_id="rt-loc-get-403", email="rt-loc-get-403@test.com")
    ac = campaigns_authenticated_client("rt-loc-get-403")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/locations/{location.slug}")
    assert response.status_code == 403


async def test_get_campaign_location_returns_404_when_not_linked(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-loc-get-404", email="rt-loc-get-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtlg0003")
    await make_location(db, owner_id=user.id, slug="tavern", name="Tavern")
    ac = campaigns_authenticated_client("rt-loc-get-404")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/locations/tavern")
    assert response.status_code == 404


async def test_get_campaign_location_returns_404_for_wrong_campaign(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-loc-get-iso", email="rt-loc-get-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="rtlga001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="rtlgb001")
    location = await make_location(db, owner_id=user.id, slug="tavern")
    await link_location(db, campaign_id=campaign_b.id, location_id=location.id)
    ac = campaigns_authenticated_client("rt-loc-get-iso")
    response = await ac.get(f"/api/v1/campaigns/{campaign_a.slug}/locations/{location.slug}")
    assert response.status_code == 404


# --- Patch ---


async def test_patch_campaign_location_returns_200(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-loc-patch-200", email="rt-loc-patch-200@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtlp0001")
    location = await make_location(db, owner_id=user.id, slug="tavern", name="Tavern", description="Original")
    await link_location(db, campaign_id=campaign.id, location_id=location.id, is_active=True, notes="Old notes")
    ac = campaigns_authenticated_client("rt-loc-patch-200")
    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/locations/{location.slug}",
        json={"is_active": False, "notes": "New notes"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Tavern"
    assert data["description"] == "Original"
    assert data["is_active"] is False
    assert data["notes"] == "New notes"


async def test_patch_campaign_location_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-loc-patch-own", email="rt-loc-patch-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtlp0002")
    location = await make_location(db, owner_id=owner.id, slug="tavern")
    await link_location(db, campaign_id=campaign.id, location_id=location.id)
    await make_user(db, supertokens_user_id="rt-loc-patch-403", email="rt-loc-patch-403@test.com")
    ac = campaigns_authenticated_client("rt-loc-patch-403")
    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/locations/{location.slug}",
        json={"notes": "New notes"},
    )
    assert response.status_code == 403


# --- Unlink ---


async def test_unlink_campaign_location_returns_204(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-loc-del-204", email="rt-loc-del-204@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtld0001")
    location = await make_location(db, owner_id=user.id, slug="tavern")
    await link_location(db, campaign_id=campaign.id, location_id=location.id)
    ac = campaigns_authenticated_client("rt-loc-del-204")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/locations/{location.slug}")
    assert response.status_code == 204


async def test_unlink_campaign_location_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-loc-del-own", email="rt-loc-del-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtld0002")
    location = await make_location(db, owner_id=owner.id, slug="tavern")
    await link_location(db, campaign_id=campaign.id, location_id=location.id)
    await make_user(db, supertokens_user_id="rt-loc-del-403", email="rt-loc-del-403@test.com")
    ac = campaigns_authenticated_client("rt-loc-del-403")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/locations/{location.slug}")
    assert response.status_code == 403


async def test_unlink_campaign_location_returns_404_when_not_linked(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-loc-del-404", email="rt-loc-del-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtld0003")
    await make_location(db, owner_id=user.id, slug="tavern", name="Tavern")
    ac = campaigns_authenticated_client("rt-loc-del-404")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/locations/tavern")
    assert response.status_code == 404


async def test_unlink_campaign_location_player_member_can_unlink(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-loc-del-plown", email="rt-loc-del-plown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtld0004")
    player = await make_user(db, supertokens_user_id="rt-loc-del-player", email="rt-loc-del-player@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    location = await make_location(db, owner_id=owner.id, slug="tavern", name="Tavern")
    await link_location(db, campaign_id=campaign.id, location_id=location.id)
    ac = campaigns_authenticated_client("rt-loc-del-player")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/locations/{location.slug}")
    assert response.status_code == 204
