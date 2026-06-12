import uuid
from collections.abc import Callable

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.campaign import Campaign
from api.models.user import User, UserAuthMethod


async def _make_user(
    db: AsyncSession,
    *,
    supertokens_user_id: str,
    email: str,
) -> User:
    user = User(email=email, display_name="Test User")
    db.add(user)
    await db.flush()
    db.add(UserAuthMethod(user_id=user.id, provider="emailpassword", supertokens_user_id=supertokens_user_id))
    await db.flush()
    return user


async def _make_campaign(
    db: AsyncSession,
    *,
    owner_id: uuid.UUID,
    name: str = "Test Campaign",
    slug_label: str = "test-campaign",
    slug_id: str = "aabbccdd",
    description: str | None = None,
) -> Campaign:
    campaign = Campaign(
        owner_id=owner_id,
        name=name,
        description=description,
        slug_label=slug_label,
        slug_id=slug_id,
    )
    db.add(campaign)
    await db.flush()
    return campaign


# --- List ---


async def test_list_campaigns_empty(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await _make_user(db, supertokens_user_id="st-list-empty", email="a@test.com")
    ac = campaigns_authenticated_client("st-list-empty")
    response = await ac.get("/api/v1/campaigns")
    assert response.status_code == 200
    assert response.json() == []


async def test_list_campaigns_returns_own_campaigns(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await _make_user(db, supertokens_user_id="st-list-own", email="b@test.com")
    await _make_campaign(db, owner_id=user.id, name="My Campaign", slug_label="my-campaign", slug_id="aabbcc01")
    ac = campaigns_authenticated_client("st-list-own")
    response = await ac.get("/api/v1/campaigns")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "My Campaign"
    assert data[0]["slug"] == "my-campaign-aabbcc01"


async def test_list_campaigns_does_not_return_others(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    other = await _make_user(db, supertokens_user_id="st-other-owner", email="other@test.com")
    await _make_campaign(db, owner_id=other.id, slug_id="otherid1")
    await _make_user(db, supertokens_user_id="st-list-none", email="c@test.com")
    ac = campaigns_authenticated_client("st-list-none")
    response = await ac.get("/api/v1/campaigns")
    assert response.status_code == 200
    assert response.json() == []


# --- Create ---


async def test_create_campaign_success(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await _make_user(db, supertokens_user_id="st-create-ok", email="d@test.com")
    ac = campaigns_authenticated_client("st-create-ok")
    response = await ac.post(
        "/api/v1/campaigns",
        json={"name": "Baldur's Gate", "description": "A great campaign", "slug_label": "baldurs-gate"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Baldur's Gate"
    assert data["description"] == "A great campaign"
    assert data["slug"].startswith("baldurs-gate-")
    assert uuid.UUID(data["id"])


async def test_create_campaign_no_description(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await _make_user(db, supertokens_user_id="st-create-nodesc", email="e@test.com")
    ac = campaigns_authenticated_client("st-create-nodesc")
    response = await ac.post(
        "/api/v1/campaigns",
        json={"name": "Minimal", "slug_label": "minimal"},
    )
    assert response.status_code == 201
    assert response.json()["description"] is None


async def test_create_campaign_empty_name_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await _make_user(db, supertokens_user_id="st-create-badname", email="f@test.com")
    ac = campaigns_authenticated_client("st-create-badname")
    response = await ac.post("/api/v1/campaigns", json={"name": "  ", "slug_label": "ok"})
    assert response.status_code == 422


async def test_create_campaign_invalid_slug_label_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await _make_user(db, supertokens_user_id="st-create-badslug", email="g@test.com")
    ac = campaigns_authenticated_client("st-create-badslug")
    response = await ac.post(
        "/api/v1/campaigns",
        json={"name": "Test", "slug_label": "-bad-slug-"},
    )
    assert response.status_code == 422


# --- Get single ---


async def test_get_campaign_by_slug(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await _make_user(db, supertokens_user_id="st-get-ok", email="h@test.com")
    await _make_campaign(db, owner_id=user.id, name="Found", slug_label="found", slug_id="getok001")
    ac = campaigns_authenticated_client("st-get-ok")
    response = await ac.get("/api/v1/campaigns/found-getok001")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Found"
    assert data["slug"] == "found-getok001"


async def test_get_campaign_stale_label_redirects(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await _make_user(db, supertokens_user_id="st-get-redir", email="i@test.com")
    await _make_campaign(db, owner_id=user.id, slug_label="new-label", slug_id="redir001")
    ac = campaigns_authenticated_client("st-get-redir")
    response = await ac.get("/api/v1/campaigns/old-label-redir001", follow_redirects=False)
    assert response.status_code == 301
    assert response.headers["location"].endswith("/api/v1/campaigns/new-label-redir001")


async def test_get_campaign_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await _make_user(db, supertokens_user_id="st-get-404", email="j@test.com")
    ac = campaigns_authenticated_client("st-get-404")
    response = await ac.get("/api/v1/campaigns/anything-notexist")
    assert response.status_code == 404


async def test_get_campaign_forbidden(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await _make_user(db, supertokens_user_id="st-owner-403", email="k@test.com")
    await _make_campaign(db, owner_id=owner.id, slug_label="secret", slug_id="forbid01")
    await _make_user(db, supertokens_user_id="st-other-403", email="l@test.com")
    ac = campaigns_authenticated_client("st-other-403")
    response = await ac.get("/api/v1/campaigns/secret-forbid01")
    assert response.status_code == 403


# --- Patch ---


async def test_patch_campaign_name(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await _make_user(db, supertokens_user_id="st-patch-name", email="m@test.com")
    await _make_campaign(db, owner_id=user.id, name="Old Name", slug_label="old-name", slug_id="patch001")
    ac = campaigns_authenticated_client("st-patch-name")
    response = await ac.patch("/api/v1/campaigns/old-name-patch001", json={"name": "New Name"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Name"
    assert data["slug"] == "old-name-patch001"  # slug_label unchanged


async def test_patch_campaign_slug_label(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await _make_user(db, supertokens_user_id="st-patch-slug", email="n@test.com")
    await _make_campaign(db, owner_id=user.id, slug_label="original", slug_id="patch002")
    ac = campaigns_authenticated_client("st-patch-slug")
    response = await ac.patch("/api/v1/campaigns/original-patch002", json={"slug_label": "renamed"})
    assert response.status_code == 200
    data = response.json()
    assert data["slug"] == "renamed-patch002"


async def test_patch_campaign_description_cleared(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await _make_user(db, supertokens_user_id="st-patch-desc", email="o@test.com")
    await _make_campaign(db, owner_id=user.id, slug_id="patch003", description="Old desc")
    ac = campaigns_authenticated_client("st-patch-desc")
    response = await ac.patch("/api/v1/campaigns/test-campaign-patch003", json={"description": None})
    assert response.status_code == 200
    assert response.json()["description"] is None


async def test_patch_campaign_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await _make_user(db, supertokens_user_id="st-patch-404", email="p@test.com")
    ac = campaigns_authenticated_client("st-patch-404")
    response = await ac.patch("/api/v1/campaigns/anything-notexist2", json={"name": "X"})
    assert response.status_code == 404


async def test_patch_campaign_forbidden(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await _make_user(db, supertokens_user_id="st-patchown-403", email="q@test.com")
    await _make_campaign(db, owner_id=owner.id, slug_id="patch004")
    await _make_user(db, supertokens_user_id="st-patchoth-403", email="r@test.com")
    ac = campaigns_authenticated_client("st-patchoth-403")
    response = await ac.patch("/api/v1/campaigns/test-campaign-patch004", json={"name": "X"})
    assert response.status_code == 403


# --- Delete ---


async def test_delete_campaign(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await _make_user(db, supertokens_user_id="st-del-ok", email="s@test.com")
    await _make_campaign(db, owner_id=user.id, slug_id="del00001")
    ac = campaigns_authenticated_client("st-del-ok")
    response = await ac.delete("/api/v1/campaigns/test-campaign-del00001")
    assert response.status_code == 204

    # Verify gone
    response2 = await ac.get("/api/v1/campaigns/test-campaign-del00001")
    assert response2.status_code == 404


async def test_delete_campaign_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    await _make_user(db, supertokens_user_id="st-del-404", email="t@test.com")
    ac = campaigns_authenticated_client("st-del-404")
    response = await ac.delete("/api/v1/campaigns/anything-notexist3")
    assert response.status_code == 404


async def test_delete_campaign_forbidden(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await _make_user(db, supertokens_user_id="st-delown-403", email="u@test.com")
    await _make_campaign(db, owner_id=owner.id, slug_id="del00002")
    await _make_user(db, supertokens_user_id="st-deloth-403", email="v@test.com")
    ac = campaigns_authenticated_client("st-deloth-403")
    response = await ac.delete("/api/v1/campaigns/test-campaign-del00002")
    assert response.status_code == 403
