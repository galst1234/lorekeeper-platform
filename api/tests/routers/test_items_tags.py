from fastapi import FastAPI, HTTPException
from httpx import AsyncClient
from pytest_mock import MockerFixture

from api.models import Campaign, CampaignMember, MemberRole
from api.routers.campaigns.dependencies import require_campaign_member
from tests.helpers import build_campaign, build_item, build_member


def _allow_member(inner_app: FastAPI, campaign: Campaign, *, role: MemberRole = MemberRole.GM) -> None:
    inner_app.dependency_overrides[require_campaign_member] = lambda: build_member(campaign_id=campaign.id, role=role)


def _forbid_member(inner_app: FastAPI) -> None:
    def _raise() -> CampaignMember:
        raise HTTPException(status_code=403, detail="Forbidden")

    inner_app.dependency_overrides[require_campaign_member] = _raise


async def test_patch_item_normalizes_and_returns_tags(
    campaigns_client: tuple[AsyncClient, FastAPI], mocker: MockerFixture
) -> None:
    async_client, inner_app = campaigns_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sunblade")
    updated = build_item(campaign_id=campaign.id, slug="sunblade", tags=["magic", "relic"])
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.items.get_item_by_slug", return_value=item)
    mock_update = mocker.patch("api.services.items.update_item", return_value=updated)

    response = await async_client.patch(
        f"/api/v1/campaigns/{campaign.slug}/items/sunblade",
        json={"tags": ["Relic", "  magic ", "magic"]},
    )

    assert response.status_code == 200
    assert response.json()["tags"] == ["magic", "relic"]
    # Route must normalize before delegating.
    _, kwargs = mock_update.await_args
    assert kwargs["tags"] == ["magic", "relic"]


async def test_patch_item_rejects_too_many_tags(
    campaigns_client: tuple[AsyncClient, FastAPI], mocker: MockerFixture
) -> None:
    async_client, inner_app = campaigns_client
    campaign = build_campaign()
    item = build_item(campaign_id=campaign.id, slug="sunblade")
    _allow_member(inner_app, campaign)
    mocker.patch("api.services.items.get_item_by_slug", return_value=item)

    response = await async_client.patch(
        f"/api/v1/campaigns/{campaign.slug}/items/sunblade",
        json={"tags": [f"tag{index}" for index in range(21)]},
    )

    assert response.status_code == 422
