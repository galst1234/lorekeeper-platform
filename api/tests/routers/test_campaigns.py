from unittest.mock import ANY, call

from fastapi import FastAPI, HTTPException
from httpx import AsyncClient
from pytest_mock import MockerFixture

from api.auth import get_current_user
from api.models import Campaign, MemberRole, User
from api.routers.campaigns.dependencies import require_campaign_owner
from api.services.campaigns import CampaignWithRole
from api.storage import ImageStorage, get_image_storage
from tests.helpers import build_campaign, build_user


def _authenticate(inner_app: FastAPI, user: User) -> None:
    inner_app.dependency_overrides[get_current_user] = lambda: user


def _allow_owner(inner_app: FastAPI, campaign: Campaign) -> None:
    inner_app.dependency_overrides[require_campaign_owner] = lambda: campaign


def _forbid_owner(inner_app: FastAPI) -> None:
    def _raise() -> Campaign:
        raise HTTPException(status_code=403, detail="Forbidden")

    inner_app.dependency_overrides[require_campaign_owner] = _raise


# --- List ---


async def test_list_campaigns_returns_200(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign()
    user = build_user()
    _authenticate(inner_app, user)
    mock_list = mocker.patch(
        "api.services.campaigns.list_campaigns",
        return_value=[CampaignWithRole(campaign=campaign, role=MemberRole.GM)],
    )

    response = await ac.get("/api/v1/campaigns")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["slug"] == campaign.slug
    mock_list.assert_awaited_once_with(ANY, user.id)


async def test_list_campaigns_includes_role_gm(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_id="rolegd01")
    _authenticate(inner_app, build_user())
    mocker.patch(
        "api.services.campaigns.list_campaigns",
        return_value=[CampaignWithRole(campaign=campaign, role=MemberRole.GM)],
    )

    response = await ac.get("/api/v1/campaigns")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["role"] == "gm"


async def test_list_campaigns_includes_role_player(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_id="rolpyl01")
    _authenticate(inner_app, build_user())
    mocker.patch(
        "api.services.campaigns.list_campaigns",
        return_value=[CampaignWithRole(campaign=campaign, role=MemberRole.PLAYER)],
    )

    response = await ac.get("/api/v1/campaigns")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["role"] == "player"


# --- Create ---


async def test_create_campaign_returns_201(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    user = build_user()
    campaign = build_campaign(slug_label="my-campaign")
    _authenticate(inner_app, user)
    mock_create = mocker.patch("api.services.campaigns.create_campaign", return_value=campaign)

    response = await ac.post("/api/v1/campaigns", json={"name": "My Campaign", "slug_label": "my-campaign"})

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["slug"] == campaign.slug
    assert data["name"] == campaign.name
    mock_create.assert_awaited_once_with(
        ANY, owner_id=user.id, name="My Campaign", description=None, slug_label="my-campaign"
    )


async def test_create_campaign_empty_name_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    _authenticate(inner_app, build_user())
    mock_create = mocker.patch("api.services.campaigns.create_campaign")

    response = await ac.post("/api/v1/campaigns", json={"name": "  ", "slug_label": "ok"})

    assert response.status_code == 422
    mock_create.assert_not_called()


async def test_create_campaign_invalid_slug_label_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    _authenticate(inner_app, build_user())
    mock_create = mocker.patch("api.services.campaigns.create_campaign")

    response = await ac.post("/api/v1/campaigns", json={"name": "Test", "slug_label": "-bad-slug-"})

    assert response.status_code == 422
    mock_create.assert_not_called()


# --- Get ---


async def test_get_campaign_stale_label_redirects(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_label="new-label", slug_id="redir001")
    _authenticate(inner_app, build_user())
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=campaign)

    response = await ac.get("/api/v1/campaigns/old-label-redir001", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"].endswith("/api/v1/campaigns/new-label-redir001")


async def test_get_campaign_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    _authenticate(inner_app, build_user())
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=None)

    response = await ac.get("/api/v1/campaigns/anything-notexist")

    assert response.status_code == 404


async def test_get_campaign_forbidden(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_label="secret", slug_id="forbid01")
    _authenticate(inner_app, build_user())
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=campaign)
    mocker.patch("api.services.campaigns.get_member_role", return_value=None)

    response = await ac.get("/api/v1/campaigns/secret-forbid01")

    assert response.status_code == 403


async def test_get_campaign_member_can_access(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_label="shared", slug_id="member01", invite_code="hidden-from-player")
    _authenticate(inner_app, build_user())
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=campaign)
    mocker.patch("api.services.campaigns.get_member_role", return_value=MemberRole.PLAYER)

    response = await ac.get("/api/v1/campaigns/shared-member01")

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "player"
    assert data["invite_code"] is None


async def test_get_campaign_owner_has_gm_role(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_label="gm-role", slug_id="gmrole01", invite_code="visible-to-gm")
    _authenticate(inner_app, build_user())
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=campaign)
    mocker.patch("api.services.campaigns.get_member_role", return_value=MemberRole.GM)

    response = await ac.get("/api/v1/campaigns/gm-role-gmrole01")

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "gm"
    assert data["invite_code"] == "visible-to-gm"


# --- Patch ---


async def test_patch_campaign_returns_200_and_updates(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_id="patchok1")
    updated = build_campaign(
        name="New Name",
        description="New description",
        slug_label="new-label",
        slug_id="patchok1",
    )
    _allow_owner(inner_app, campaign)
    mock_update = mocker.patch("api.services.campaigns.update_campaign", return_value=updated)

    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}",
        json={"name": "New Name", "description": "New description", "slug_label": "new-label"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["description"] == "New description"
    assert data["slug"] == updated.slug
    mock_update.assert_awaited_once_with(
        ANY, campaign, name="New Name", description="New description", slug_label="new-label"
    )


async def test_patch_campaign_null_name_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_id="nullnm01")
    _allow_owner(inner_app, campaign)
    mock_update = mocker.patch("api.services.campaigns.update_campaign")

    response = await ac.patch(f"/api/v1/campaigns/{campaign.slug}", json={"name": None})

    assert response.status_code == 422
    mock_update.assert_not_called()


async def test_patch_campaign_null_slug_label_rejected(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_id="nullsl01")
    _allow_owner(inner_app, campaign)
    mock_update = mocker.patch("api.services.campaigns.update_campaign")

    response = await ac.patch(f"/api/v1/campaigns/{campaign.slug}", json={"slug_label": None})

    assert response.status_code == 422
    mock_update.assert_not_called()


async def test_patch_campaign_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    _authenticate(inner_app, build_user())
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=None)

    response = await ac.patch("/api/v1/campaigns/anything-notexist2", json={"name": "X"})

    assert response.status_code == 404


async def test_patch_campaign_forbidden(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    _forbid_owner(inner_app)
    mock_update = mocker.patch("api.services.campaigns.update_campaign")

    response = await ac.patch("/api/v1/campaigns/test-campaign-patch004", json={"name": "X"})

    assert response.status_code == 403
    mock_update.assert_not_called()


# --- Delete ---


async def test_delete_campaign_returns_204(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_id="del00001")
    _allow_owner(inner_app, campaign)
    image_storage = mocker.create_autospec(ImageStorage, instance=True)
    inner_app.dependency_overrides[get_image_storage] = lambda: image_storage
    mock_delete = mocker.patch("api.services.campaigns.delete_campaign")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}")

    assert response.status_code == 204
    assert response.content == b""
    mock_delete.assert_awaited_once_with(ANY, campaign, image_storage)


async def test_delete_campaign_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    _authenticate(inner_app, build_user())
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=None)

    response = await ac.delete("/api/v1/campaigns/anything-notexist3")

    assert response.status_code == 404


async def test_delete_campaign_forbidden(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    _forbid_owner(inner_app)
    mock_delete = mocker.patch("api.services.campaigns.delete_campaign")

    response = await ac.delete("/api/v1/campaigns/test-campaign-del00002")

    assert response.status_code == 403
    mock_delete.assert_not_called()


# --- POST /campaigns/{slug}/invites ---


async def test_create_invite_returns_200_with_code(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_id="invgen01")
    updated = build_campaign(slug_id="invgen01", invite_code="dX9kLmN2pQrS4tUvWxYz")
    _allow_owner(inner_app, campaign)
    mock_generate = mocker.patch("api.services.campaigns.generate_invite", return_value=updated)

    response = await ac.post(f"/api/v1/campaigns/{campaign.slug}/invites")

    assert response.status_code == 200
    data = response.json()
    assert data["invite_code"] == "dX9kLmN2pQrS4tUvWxYz"
    assert data["invite_url"] == f"/campaigns/{updated.slug}/invites/dX9kLmN2pQrS4tUvWxYz"
    mock_generate.assert_awaited_once_with(ANY, campaign)


async def test_create_invite_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    _authenticate(inner_app, build_user())
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=None)

    response = await ac.post("/api/v1/campaigns/nothing-notexist/invites")

    assert response.status_code == 404


async def test_create_invite_forbidden(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    _forbid_owner(inner_app)
    mock_generate = mocker.patch("api.services.campaigns.generate_invite")

    response = await ac.post("/api/v1/campaigns/test-campaign-invfrb01/invites")

    assert response.status_code == 403
    mock_generate.assert_not_called()


# --- DELETE /campaigns/{slug}/invites ---


async def test_delete_invite_returns_204(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_id="invdel01", invite_code="torevoke")
    _allow_owner(inner_app, campaign)
    mock_revoke = mocker.patch("api.services.campaigns.revoke_invite")

    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/invites")

    assert response.status_code == 204
    mock_revoke.assert_awaited_once_with(ANY, campaign)


async def test_delete_invite_not_found(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    _authenticate(inner_app, build_user())
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=None)

    response = await ac.delete("/api/v1/campaigns/nothing-notexist2/invites")

    assert response.status_code == 404


async def test_delete_invite_forbidden(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    _forbid_owner(inner_app)
    mock_revoke = mocker.patch("api.services.campaigns.revoke_invite")

    response = await ac.delete("/api/v1/campaigns/test-campaign-invdfb01/invites")

    assert response.status_code == 403
    mock_revoke.assert_not_called()


# --- GET /campaigns/{slug}/invites/{invite_code} ---


async def test_get_join_preview_returns_campaign_info(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_id="jnprev01", invite_code="validcode")
    _authenticate(inner_app, build_user())
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=campaign)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/invites/validcode")

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Campaign"
    assert data["slug"] == campaign.slug


async def test_get_join_preview_wrong_code_returns_404(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_id="jnpbad01", invite_code="rightcode")
    _authenticate(inner_app, build_user())
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=campaign)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/invites/wrongcode")

    assert response.status_code == 404


async def test_get_join_preview_no_invite_returns_404(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_id="jnnoinv1", invite_code=None)
    _authenticate(inner_app, build_user())
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=campaign)

    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/invites/anycode")

    assert response.status_code == 404


async def test_get_join_preview_stale_slug_redirects(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_label="new-label", slug_id="jnrdr001", invite_code="thecode")
    _authenticate(inner_app, build_user())
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=campaign)

    response = await ac.get("/api/v1/campaigns/old-label-jnrdr001/invites/thecode", follow_redirects=False)

    assert response.status_code == 307
    assert "new-label-jnrdr001" in response.headers["location"]
    assert "thecode" in response.headers["location"]


# --- POST /campaigns/{slug}/invites/{invite_code} (join) ---


async def test_post_join_adds_member_returns_campaign(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_id="rtjoin01", invite_code="joinme01")
    user = build_user()
    _authenticate(inner_app, user)
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=campaign)
    mock_join = mocker.patch("api.services.campaigns.join_campaign", return_value=True)
    mocker.patch("api.services.campaigns.get_member_role", return_value=MemberRole.PLAYER)

    response = await ac.post(f"/api/v1/campaigns/{campaign.slug}/invites/joinme01")

    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "player"
    assert data["slug"] == campaign.slug
    mock_join.assert_awaited_once_with(ANY, campaign, user.id, "joinme01")


async def test_post_join_wrong_code_returns_404(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_id="rtjbad01", invite_code="rightone")
    _authenticate(inner_app, build_user())
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=campaign)
    mock_join = mocker.patch("api.services.campaigns.join_campaign")

    response = await ac.post(f"/api/v1/campaigns/{campaign.slug}/invites/wrongone")

    assert response.status_code == 404
    mock_join.assert_not_called()


async def test_post_join_idempotent(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    """Joining with the same invite code twice (e.g. a retried request) succeeds both times

    with the same result, because `join_campaign`'s `on_conflict_do_nothing` insert makes the
    second call a no-op rather than an error.
    """
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_id="rtjidem1", invite_code="idemcode")
    user = build_user()
    _authenticate(inner_app, user)
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=campaign)
    mock_join = mocker.patch("api.services.campaigns.join_campaign", return_value=True)
    mocker.patch("api.services.campaigns.get_member_role", return_value=MemberRole.PLAYER)

    first_response = await ac.post(f"/api/v1/campaigns/{campaign.slug}/invites/idemcode")
    second_response = await ac.post(f"/api/v1/campaigns/{campaign.slug}/invites/idemcode")

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json() == second_response.json()
    assert mock_join.await_count == 2
    assert mock_join.await_args_list == [
        call(ANY, campaign, user.id, "idemcode"),
        call(ANY, campaign, user.id, "idemcode"),
    ]


async def test_post_join_owner_has_gm_role_in_response(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_id="rtjgm001", invite_code="ownjoin1")
    _authenticate(inner_app, build_user())
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=campaign)
    mocker.patch("api.services.campaigns.join_campaign", return_value=True)
    mocker.patch("api.services.campaigns.get_member_role", return_value=MemberRole.GM)

    response = await ac.post(f"/api/v1/campaigns/{campaign.slug}/invites/ownjoin1")

    assert response.status_code == 200
    assert response.json()["role"] == "gm"


async def test_post_join_revoked_code_returns_404(
    campaigns_client: tuple[AsyncClient, FastAPI],
    mocker: MockerFixture,
) -> None:
    ac, inner_app = campaigns_client
    campaign = build_campaign(slug_id="rtjrvk01", invite_code=None)
    _authenticate(inner_app, build_user())
    mocker.patch("api.services.campaigns.get_campaign_by_slug", return_value=campaign)
    mock_join = mocker.patch("api.services.campaigns.join_campaign")

    response = await ac.post(f"/api/v1/campaigns/{campaign.slug}/invites/torevoke")

    assert response.status_code == 404
    mock_join.assert_not_called()
