from unittest.mock import ANY

from fastapi import FastAPI, HTTPException
from httpx import AsyncClient
from pydantic_core import MISSING
from pytest_mock import MockerFixture

from api.models import Campaign, CampaignMember, MemberRole
from api.routers.campaigns.dependencies import require_campaign_member
from api.services.locations import LocationSlugConflictError
from tests.helpers import build_campaign, build_location, build_member


def _allow_member(inner_app: FastAPI, campaign: Campaign, *, role: MemberRole = MemberRole.GM) -> None:
    inner_app.dependency_overrides[require_campaign_member] = lambda: build_member(campaign_id=campaign.id, role=role)


def _forbid_member(inner_app: FastAPI) -> None:
    def _raise() -> CampaignMember:
        raise HTTPException(status_code=403, detail="Forbidden")

    inner_app.dependency_overrides[require_campaign_member] = _raise


# --- List ---


async def test_list_locations_returns_200(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    location = build_location(campaign_id=campaign.id, slug="tavern", name="Tavern")
    _allow_member(inner_app, campaign)
    mock_list = mocker.patch("api.services.locations.list_locations", return_value=[location])

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/locations")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Tavern"
    assert data[0]["slug"] == "tavern"
    mock_list.assert_awaited_once_with(ANY, campaign.id)


async def test_list_locations_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_list = mocker.patch("api.services.locations.list_locations")

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/locations")

    assert response.status_code == 403
    mock_list.assert_not_called()


# --- Create ---


async def test_create_location_returns_201(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    location = build_location(campaign_id=campaign.id, slug="tavern", name="Tavern", description=None)
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.locations.create_location", return_value=location)

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/locations",
        json={"slug": "tavern", "name": "Tavern"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "tavern"
    assert data["name"] == "Tavern"
    assert data["description"] is None
    mock_create.assert_awaited_once_with(ANY, campaign_id=campaign.id, slug="tavern", name="Tavern", description=None)


async def test_create_location_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_create = mocker.patch("api.services.locations.create_location")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/locations",
        json={"slug": "tavern", "name": "Tavern"},
    )

    assert response.status_code == 403
    mock_create.assert_not_called()


async def test_create_location_empty_name_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.locations.create_location")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/locations",
        json={"slug": "tavern", "name": "  "},
    )

    assert response.status_code == 422
    mock_create.assert_not_called()


async def test_create_location_invalid_slug_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.locations.create_location")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/locations",
        json={"slug": "Tavern Square", "name": "Tavern"},
    )

    assert response.status_code == 422
    mock_create.assert_not_called()


async def test_create_location_reserved_slug_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.locations.create_location")

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/locations",
        json={"slug": "new", "name": "New Location"},
    )

    assert response.status_code == 422
    mock_create.assert_not_called()


async def test_create_location_slug_conflict_returns_409(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_create = mocker.patch("api.services.locations.create_location", side_effect=LocationSlugConflictError())

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/locations",
        json={"slug": "tavern", "name": "Another Tavern"},
    )

    assert response.status_code == 409
    mock_create.assert_awaited_once_with(
        ANY, campaign_id=campaign.id, slug="tavern", name="Another Tavern", description=None
    )


async def test_create_location_player_member_can_create(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    location = build_location(campaign_id=campaign.id, slug="tavern", name="Tavern")
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_create = mocker.patch("api.services.locations.create_location", return_value=location)

    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/locations",
        json={"slug": "tavern", "name": "Tavern"},
    )

    assert response.status_code == 201
    mock_create.assert_awaited_once_with(ANY, campaign_id=campaign.id, slug="tavern", name="Tavern", description=None)


# --- Get ---


async def test_get_location_returns_200(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    location = build_location(campaign_id=campaign.id, slug="tavern", name="Tavern", description="First stop")
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.locations.get_location_by_slug", return_value=location)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/locations/tavern")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Tavern"
    assert data["slug"] == "tavern"
    assert data["description"] == "First stop"
    mock_get.assert_awaited_once_with(ANY, campaign.id, "tavern")


async def test_get_location_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_get = mocker.patch("api.services.locations.get_location_by_slug")

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/locations/tavern")

    assert response.status_code == 403
    mock_get.assert_not_called()


async def test_get_location_returns_404_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.locations.get_location_by_slug", return_value=None)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/locations/nonexistent-location")

    assert response.status_code == 404
    mock_get.assert_awaited_once_with(ANY, campaign.id, "nonexistent-location")


async def test_get_location_returns_404_for_wrong_campaign(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.locations.get_location_by_slug", return_value=None)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/locations/tavern")

    assert response.status_code == 404
    mock_get.assert_awaited_once_with(ANY, campaign.id, "tavern")


# --- Patch ---


async def test_patch_location_returns_200(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    location = build_location(campaign_id=campaign.id, slug="tavern", name="Tavern", description="Original")
    updated = build_location(
        campaign_id=campaign.id, slug="tavern", name="Rebuilt Tavern", description="Updated description"
    )
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.locations.get_location_by_slug", return_value=location)
    mock_update = mocker.patch("api.services.locations.update_location", return_value=updated)

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/locations/tavern",
        json={"name": "Rebuilt Tavern", "description": "Updated description"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Rebuilt Tavern"
    assert data["description"] == "Updated description"
    mock_get.assert_awaited_once_with(ANY, campaign.id, "tavern")
    mock_update.assert_awaited_once_with(ANY, location, name="Rebuilt Tavern", description="Updated description")


async def test_patch_location_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_get = mocker.patch("api.services.locations.get_location_by_slug")
    mock_update = mocker.patch("api.services.locations.update_location")

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/locations/tavern",
        json={"name": "Rebuilt Tavern"},
    )

    assert response.status_code == 403
    mock_get.assert_not_called()
    mock_update.assert_not_called()


async def test_patch_location_returns_404_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.locations.get_location_by_slug", return_value=None)
    mock_update = mocker.patch("api.services.locations.update_location")

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/locations/nonexistent-location",
        json={"name": "Rebuilt Tavern"},
    )

    assert response.status_code == 404
    mock_get.assert_awaited_once_with(ANY, campaign.id, "nonexistent-location")
    mock_update.assert_not_called()


async def test_patch_location_returns_404_for_wrong_campaign(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.locations.get_location_by_slug", return_value=None)
    mock_update = mocker.patch("api.services.locations.update_location")

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/locations/tavern",
        json={"name": "Rebuilt Tavern"},
    )

    assert response.status_code == 404
    mock_get.assert_awaited_once_with(ANY, campaign.id, "tavern")
    mock_update.assert_not_called()


async def test_patch_location_player_member_can_patch(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    location = build_location(campaign_id=campaign.id, slug="tavern")
    updated = build_location(campaign_id=campaign.id, slug="tavern", description="Player update")
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_get = mocker.patch("api.services.locations.get_location_by_slug", return_value=location)
    mock_update = mocker.patch("api.services.locations.update_location", return_value=updated)

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/locations/tavern",
        json={"description": "Player update"},
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Player update"
    mock_get.assert_awaited_once_with(ANY, campaign.id, "tavern")
    mock_update.assert_awaited_once_with(ANY, location, name=MISSING, description="Player update")


# --- Delete ---


async def test_delete_location_returns_204(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    location = build_location(campaign_id=campaign.id, slug="tavern")
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.locations.get_location_by_slug", return_value=location)
    mock_delete = mocker.patch("api.services.locations.delete_location")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/locations/tavern")

    assert response.status_code == 204
    mock_get.assert_awaited_once_with(ANY, campaign.id, "tavern")
    mock_delete.assert_awaited_once_with(ANY, location)


async def test_delete_location_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_get = mocker.patch("api.services.locations.get_location_by_slug")
    mock_delete = mocker.patch("api.services.locations.delete_location")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/locations/tavern")

    assert response.status_code == 403
    mock_get.assert_not_called()
    mock_delete.assert_not_called()


async def test_delete_location_returns_404_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.locations.get_location_by_slug", return_value=None)
    mock_delete = mocker.patch("api.services.locations.delete_location")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/locations/nonexistent-location")

    assert response.status_code == 404
    mock_get.assert_awaited_once_with(ANY, campaign.id, "nonexistent-location")
    mock_delete.assert_not_called()


async def test_delete_location_returns_404_for_wrong_campaign(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_get = mocker.patch("api.services.locations.get_location_by_slug", return_value=None)
    mock_delete = mocker.patch("api.services.locations.delete_location")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/locations/tavern")

    assert response.status_code == 404
    mock_get.assert_awaited_once_with(ANY, campaign.id, "tavern")
    mock_delete.assert_not_called()


async def test_delete_location_player_member_can_delete(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    location = build_location(campaign_id=campaign.id, slug="tavern")
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_get = mocker.patch("api.services.locations.get_location_by_slug", return_value=location)
    mock_delete = mocker.patch("api.services.locations.delete_location")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/locations/tavern")

    assert response.status_code == 204
    mock_get.assert_awaited_once_with(ANY, campaign.id, "tavern")
    mock_delete.assert_awaited_once_with(ANY, location)
