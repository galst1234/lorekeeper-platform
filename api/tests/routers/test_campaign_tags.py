from fastapi import FastAPI
from httpx import AsyncClient
from pytest_mock import MockerFixture

from api.models import Campaign, MemberRole
from api.routers.campaigns.dependencies import require_campaign_member
from tests.helpers import build_campaign, build_member


def _allow_member(inner_app: FastAPI, campaign: Campaign, *, role: MemberRole = MemberRole.GM) -> None:
    inner_app.dependency_overrides[require_campaign_member] = lambda: build_member(campaign_id=campaign.id, role=role)


async def test_list_campaign_tags_returns_sorted_union(
    campaigns_client: tuple[AsyncClient, FastAPI], mocker: MockerFixture
) -> None:
    async_client, inner_app = campaigns_client
    campaign = build_campaign()
    _allow_member(inner_app, campaign)
    mock_list = mocker.patch("api.services.tags.list_campaign_tags", return_value=["magic", "relic", "villain"])

    response = await async_client.get(f"/api/v1/campaigns/{campaign.slug}/tags")

    assert response.status_code == 200
    assert response.json() == {"tags": ["magic", "relic", "villain"]}
    mock_list.assert_awaited_once()
