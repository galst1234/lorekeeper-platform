from collections.abc import Callable

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers import make_campaign, make_user

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
