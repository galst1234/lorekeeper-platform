from collections.abc import Callable

from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Campaign
from tests.helpers import make_campaign, make_member, make_user

# --- List ---


async def test_list_campaigns_returns_200(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await make_user(db, supertokens_user_id="rt-list-200", email="rt-list-200@test.com")
    ac = campaigns_authenticated_client("rt-list-200")
    response = await ac.get("/api/v1/campaigns")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# --- Create ---


async def test_create_campaign_returns_201(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await make_user(db, supertokens_user_id="rt-create-201", email="rt-create-201@test.com")
    ac = campaigns_authenticated_client("rt-create-201")
    response = await ac.post(
        "/api/v1/campaigns",
        json={"name": "My Campaign", "slug_label": "my-campaign"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert "slug" in data
    assert "name" in data


async def test_create_campaign_empty_name_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await make_user(db, supertokens_user_id="rt-create-badname", email="rt-create-badname@test.com")
    ac = campaigns_authenticated_client("rt-create-badname")
    response = await ac.post("/api/v1/campaigns", json={"name": "  ", "slug_label": "ok"})
    assert response.status_code == 422


async def test_create_campaign_invalid_slug_label_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await make_user(db, supertokens_user_id="rt-create-badslug", email="rt-create-badslug@test.com")
    ac = campaigns_authenticated_client("rt-create-badslug")
    response = await ac.post(
        "/api/v1/campaigns",
        json={"name": "Test", "slug_label": "-bad-slug-"},
    )
    assert response.status_code == 422


# --- Get ---


async def test_get_campaign_stale_label_redirects(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-get-redir", email="rt-get-redir@test.com")
    await make_campaign(db, owner_id=user.id, slug_label="new-label", slug_id="redir001")
    ac = campaigns_authenticated_client("rt-get-redir")
    response = await ac.get("/api/v1/campaigns/old-label-redir001", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"].endswith("/api/v1/campaigns/new-label-redir001")


async def test_get_campaign_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await make_user(db, supertokens_user_id="rt-get-404", email="rt-get-404@test.com")
    ac = campaigns_authenticated_client("rt-get-404")
    response = await ac.get("/api/v1/campaigns/anything-notexist")
    assert response.status_code == 404


async def test_get_campaign_forbidden(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-get-owner", email="rt-get-owner@test.com")
    await make_campaign(db, owner_id=owner.id, slug_label="secret", slug_id="forbid01")
    await make_user(db, supertokens_user_id="rt-get-other", email="rt-get-other@test.com")
    ac = campaigns_authenticated_client("rt-get-other")
    response = await ac.get("/api/v1/campaigns/secret-forbid01")
    assert response.status_code == 403


async def test_get_campaign_member_can_access(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-get-mem-own", email="rt-get-mem-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_label="shared", slug_id="member01")
    player = await make_user(db, supertokens_user_id="rt-get-mem-ply", email="rt-get-mem-ply@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    ac = campaigns_authenticated_client("rt-get-mem-ply")
    response = await ac.get("/api/v1/campaigns/shared-member01")
    assert response.status_code == 200
    assert response.json()["role"] == "player"


# --- Patch ---


async def test_patch_campaign_null_name_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-patch-nullname", email="rt-patch-nullname@test.com")
    await make_campaign(db, owner_id=user.id, slug_id="nullnm01")
    ac = campaigns_authenticated_client("rt-patch-nullname")
    response = await ac.patch("/api/v1/campaigns/test-campaign-nullnm01", json={"name": None})
    assert response.status_code == 422


async def test_patch_campaign_null_slug_label_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-patch-nullslug", email="rt-patch-nullslug@test.com")
    await make_campaign(db, owner_id=user.id, slug_id="nullsl01")
    ac = campaigns_authenticated_client("rt-patch-nullslug")
    response = await ac.patch("/api/v1/campaigns/test-campaign-nullsl01", json={"slug_label": None})
    assert response.status_code == 422


async def test_patch_campaign_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await make_user(db, supertokens_user_id="rt-patch-404", email="rt-patch-404@test.com")
    ac = campaigns_authenticated_client("rt-patch-404")
    response = await ac.patch("/api/v1/campaigns/anything-notexist2", json={"name": "X"})
    assert response.status_code == 404


async def test_patch_campaign_forbidden(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-patch-owner", email="rt-patch-owner@test.com")
    await make_campaign(db, owner_id=owner.id, slug_id="patch004")
    await make_user(db, supertokens_user_id="rt-patch-other", email="rt-patch-other@test.com")
    ac = campaigns_authenticated_client("rt-patch-other")
    response = await ac.patch("/api/v1/campaigns/test-campaign-patch004", json={"name": "X"})
    assert response.status_code == 403


# --- Delete ---


async def test_delete_campaign_returns_204(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-del-204", email="rt-del-204@test.com")
    await make_campaign(db, owner_id=user.id, slug_id="del00001")
    ac = campaigns_authenticated_client("rt-del-204")
    response = await ac.delete("/api/v1/campaigns/test-campaign-del00001")
    assert response.status_code == 204
    assert response.content == b""


async def test_delete_campaign_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await make_user(db, supertokens_user_id="rt-del-404", email="rt-del-404@test.com")
    ac = campaigns_authenticated_client("rt-del-404")
    response = await ac.delete("/api/v1/campaigns/anything-notexist3")
    assert response.status_code == 404


async def test_delete_campaign_forbidden(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-del-owner", email="rt-del-owner@test.com")
    await make_campaign(db, owner_id=owner.id, slug_id="del00002")
    await make_user(db, supertokens_user_id="rt-del-other", email="rt-del-other@test.com")
    ac = campaigns_authenticated_client("rt-del-other")
    response = await ac.delete("/api/v1/campaigns/test-campaign-del00002")
    assert response.status_code == 403


# --- List with role ---


async def test_list_campaigns_includes_role_gm(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-lst-role-gm", email="rt-lst-role-gm@test.com")
    await make_campaign(db, owner_id=user.id, slug_id="rolegd01")
    ac = campaigns_authenticated_client("rt-lst-role-gm")
    response = await ac.get("/api/v1/campaigns")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["role"] == "gm"


async def test_list_campaigns_includes_role_player(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-lst-role-own", email="rt-lst-role-own@test.com")
    player = await make_user(db, supertokens_user_id="rt-lst-role-ply", email="rt-lst-role-ply@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rolpyl01")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    ac = campaigns_authenticated_client("rt-lst-role-ply")
    response = await ac.get("/api/v1/campaigns")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["role"] == "player"


# --- POST /campaigns/{slug}/invite ---


async def test_create_invite_returns_200_with_code(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-inv-gen-ok", email="rt-inv-gen-ok@test.com")
    await make_campaign(db, owner_id=user.id, slug_id="invgen01")
    ac = campaigns_authenticated_client("rt-inv-gen-ok")
    response = await ac.post("/api/v1/campaigns/test-campaign-invgen01/invite")
    assert response.status_code == 200
    data = response.json()
    assert "invite_code" in data
    assert data["invite_url"] == f"/campaigns/test-campaign-invgen01/join/{data['invite_code']}"


async def test_create_invite_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await make_user(db, supertokens_user_id="rt-inv-gen-404", email="rt-inv-gen-404@test.com")
    ac = campaigns_authenticated_client("rt-inv-gen-404")
    response = await ac.post("/api/v1/campaigns/nothing-notexist/invite")
    assert response.status_code == 404


async def test_create_invite_forbidden(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-inv-gen-own", email="rt-inv-gen-own@test.com")
    await make_campaign(db, owner_id=owner.id, slug_id="invfrb01")
    await make_user(db, supertokens_user_id="rt-inv-gen-oth", email="rt-inv-gen-oth@test.com")
    ac = campaigns_authenticated_client("rt-inv-gen-oth")
    response = await ac.post("/api/v1/campaigns/test-campaign-invfrb01/invite")
    assert response.status_code == 403


# --- DELETE /campaigns/{slug}/invite ---


async def test_delete_invite_returns_204(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-inv-del-ok", email="rt-inv-del-ok@test.com")
    await make_campaign(db, owner_id=user.id, slug_id="invdel01", invite_code="torevoke")
    ac = campaigns_authenticated_client("rt-inv-del-ok")
    response = await ac.delete("/api/v1/campaigns/test-campaign-invdel01/invite")
    assert response.status_code == 204


async def test_delete_invite_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await make_user(db, supertokens_user_id="rt-inv-del-404", email="rt-inv-del-404@test.com")
    ac = campaigns_authenticated_client("rt-inv-del-404")
    response = await ac.delete("/api/v1/campaigns/nothing-notexist2/invite")
    assert response.status_code == 404


async def test_delete_invite_forbidden(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-inv-del-own", email="rt-inv-del-own@test.com")
    await make_campaign(db, owner_id=owner.id, slug_id="invdfb01", invite_code="torevoke")
    await make_user(db, supertokens_user_id="rt-inv-del-oth", email="rt-inv-del-oth@test.com")
    ac = campaigns_authenticated_client("rt-inv-del-oth")
    response = await ac.delete("/api/v1/campaigns/test-campaign-invdfb01/invite")
    assert response.status_code == 403


# --- GET /campaigns/{slug}/join/{invite_code} ---


async def test_get_join_preview_returns_campaign_info(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-jnpv-own", email="rt-jnpv-own@test.com")
    await make_campaign(db, owner_id=owner.id, slug_id="jnprev01", invite_code="validcode")
    await make_user(db, supertokens_user_id="rt-jnpv-ply", email="rt-jnpv-ply@test.com")
    ac = campaigns_authenticated_client("rt-jnpv-ply")
    response = await ac.get("/api/v1/campaigns/test-campaign-jnprev01/join/validcode")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Campaign"
    assert "slug" in data


async def test_get_join_preview_wrong_code_returns_404(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-jnpv-bad", email="rt-jnpv-bad@test.com")
    await make_campaign(db, owner_id=owner.id, slug_id="jnpbad01", invite_code="rightcode")
    await make_user(db, supertokens_user_id="rt-jnpv-bply", email="rt-jnpv-bply@test.com")
    ac = campaigns_authenticated_client("rt-jnpv-bply")
    response = await ac.get("/api/v1/campaigns/test-campaign-jnpbad01/join/wrongcode")
    assert response.status_code == 404


async def test_get_join_preview_no_invite_returns_404(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-jnpv-noinv", email="rt-jnpv-noinv@test.com")
    await make_campaign(db, owner_id=owner.id, slug_id="jnnoinv1")
    await make_user(db, supertokens_user_id="rt-jnpv-nply", email="rt-jnpv-nply@test.com")
    ac = campaigns_authenticated_client("rt-jnpv-nply")
    response = await ac.get("/api/v1/campaigns/test-campaign-jnnoinv1/join/anycode")
    assert response.status_code == 404


async def test_get_join_preview_stale_slug_redirects(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-jnpv-rdr", email="rt-jnpv-rdr@test.com")
    await make_campaign(db, owner_id=owner.id, slug_label="new-label", slug_id="jnrdr001", invite_code="thecode")
    await make_user(db, supertokens_user_id="rt-jnpv-rply", email="rt-jnpv-rply@test.com")
    ac = campaigns_authenticated_client("rt-jnpv-rply")
    response = await ac.get("/api/v1/campaigns/old-label-jnrdr001/join/thecode", follow_redirects=False)
    assert response.status_code == 307
    assert "new-label-jnrdr001" in response.headers["location"]
    assert "thecode" in response.headers["location"]


# --- POST /campaigns/{slug}/join/{invite_code} ---


async def test_post_join_adds_member_returns_campaign(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-join-own", email="rt-join-own@test.com")
    await make_campaign(db, owner_id=owner.id, slug_id="rtjoin01", invite_code="joinme01")
    await make_user(db, supertokens_user_id="rt-join-ply", email="rt-join-ply@test.com")
    ac = campaigns_authenticated_client("rt-join-ply")
    response = await ac.post("/api/v1/campaigns/test-campaign-rtjoin01/join/joinme01")
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "player"
    assert "slug" in data


async def test_post_join_wrong_code_returns_404(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-join-bad", email="rt-join-bad@test.com")
    await make_campaign(db, owner_id=owner.id, slug_id="rtjbad01", invite_code="rightone")
    await make_user(db, supertokens_user_id="rt-join-bply", email="rt-join-bply@test.com")
    ac = campaigns_authenticated_client("rt-join-bply")
    response = await ac.post("/api/v1/campaigns/test-campaign-rtjbad01/join/wrongone")
    assert response.status_code == 404


async def test_post_join_idempotent(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-join-iown", email="rt-join-iown@test.com")
    await make_campaign(db, owner_id=owner.id, slug_id="rtjidem1", invite_code="idemcode")
    await make_user(db, supertokens_user_id="rt-join-iply", email="rt-join-iply@test.com")
    ac = campaigns_authenticated_client("rt-join-iply")
    await ac.post("/api/v1/campaigns/test-campaign-rtjidem1/join/idemcode")
    response = await ac.post("/api/v1/campaigns/test-campaign-rtjidem1/join/idemcode")
    assert response.status_code == 200


async def test_get_campaign_owner_has_gm_role(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-get-gm-role", email="rt-get-gm-role@test.com")
    await make_campaign(db, owner_id=user.id, slug_label="gm-role", slug_id="gmrole01")
    ac = campaigns_authenticated_client("rt-get-gm-role")
    response = await ac.get("/api/v1/campaigns/gm-role-gmrole01")
    assert response.status_code == 200
    assert response.json()["role"] == "gm"


async def test_post_join_owner_has_gm_role_in_response(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-join-gm-own", email="rt-join-gm-own@test.com")
    await make_campaign(db, owner_id=owner.id, slug_id="rtjgm001", invite_code="ownjoin1")
    ac = campaigns_authenticated_client("rt-join-gm-own")
    response = await ac.post("/api/v1/campaigns/test-campaign-rtjgm001/join/ownjoin1")
    assert response.status_code == 200
    assert response.json()["role"] == "gm"


async def test_post_join_revoked_code_returns_404(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-join-rvk", email="rt-join-rvk@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtjrvk01", invite_code="torevoke")
    await make_user(db, supertokens_user_id="rt-join-rply", email="rt-join-rply@test.com")
    await db.execute(update(Campaign).where(Campaign.id == campaign.id).values(invite_code=None))
    await db.commit()
    ac = campaigns_authenticated_client("rt-join-rply")
    response = await ac.post(f"/api/v1/campaigns/{campaign.slug}/join/torevoke")
    assert response.status_code == 404
