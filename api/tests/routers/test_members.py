from unittest.mock import ANY

from fastapi import FastAPI, HTTPException
from httpx import AsyncClient
from pytest_mock import MockerFixture

from api.models import Campaign, CampaignMember, MemberRole
from api.routers.campaigns.dependencies import require_campaign_member
from tests.helpers import build_campaign, build_member, build_user


def _allow_member(inner_app: FastAPI, campaign: Campaign, *, role: MemberRole = MemberRole.GM) -> None:
    inner_app.dependency_overrides[require_campaign_member] = lambda: build_member(campaign_id=campaign.id, role=role)


def _forbid_member(inner_app: FastAPI) -> None:
    def _raise() -> CampaignMember:
        raise HTTPException(status_code=403, detail="Forbidden")

    inner_app.dependency_overrides[require_campaign_member] = _raise


async def test_list_members_returns_200(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    owner = build_user(display_name="The Dungeon Master")
    player = build_user(display_name="Frodo")
    owner_member = build_member(campaign_id=campaign.id, user_id=owner.id, role=MemberRole.GM)
    player_member = build_member(campaign_id=campaign.id, user_id=player.id, role=MemberRole.PLAYER)
    _allow_member(inner_app, campaign)
    mock_list = mocker.patch(
        "api.services.campaigns.list_members_with_users",
        return_value=[(owner_member, owner), (player_member, player)],
    )

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/members")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["user_id"] == str(owner.id)
    assert data[0]["display_name"] == "The Dungeon Master"
    assert data[0]["role"] == "gm"
    assert data[0]["joined_at"] == owner_member.joined_at.isoformat().replace("+00:00", "Z")
    assert data[1]["user_id"] == str(player.id)
    assert data[1]["display_name"] == "Frodo"
    assert data[1]["role"] == "player"
    assert data[1]["joined_at"] == player_member.joined_at.isoformat().replace("+00:00", "Z")
    mock_list.assert_awaited_once_with(ANY, campaign.id)


async def test_list_members_returns_200_for_player_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign, role=MemberRole.PLAYER)
    mock_list = mocker.patch("api.services.campaigns.list_members_with_users", return_value=[])

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/members")

    assert response.status_code == 200
    assert response.json() == []
    mock_list.assert_awaited_once_with(ANY, campaign.id)


async def test_list_members_returns_403_for_non_member(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    _forbid_member(inner_app)
    mock_list = mocker.patch("api.services.campaigns.list_members_with_users")

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/members")

    assert response.status_code == 403
    mock_list.assert_not_called()
