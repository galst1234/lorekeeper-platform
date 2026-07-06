from collections.abc import Callable

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.helpers import make_campaign, make_character, make_member, make_user

# --- List ---


async def test_list_characters_returns_200(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-list-200", email="rt-chr-list-200@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcl0001")
    await make_character(db, campaign_id=campaign.id, slug="aria", name="Aria")
    ac = campaigns_authenticated_client("rt-chr-list-200")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "Aria"
    assert data[0]["slug"] == "aria"
    assert data[0]["character_type"] == "pc"


async def test_list_characters_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-list-own", email="rt-chr-list-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcl0002")
    await make_user(db, supertokens_user_id="rt-chr-list-403", email="rt-chr-list-403@test.com")
    ac = campaigns_authenticated_client("rt-chr-list-403")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters")
    assert response.status_code == 403


# --- Create ---


async def test_create_character_returns_201(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-cr-201", email="rt-chr-cr-201@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0001")
    ac = campaigns_authenticated_client("rt-chr-cr-201")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "pc"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["slug"] == "aria"
    assert data["name"] == "Aria"
    assert data["character_type"] == "pc"
    assert data["description"] is None


async def test_create_character_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-cr-own", email="rt-chr-cr-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcc0002")
    await make_user(db, supertokens_user_id="rt-chr-cr-403", email="rt-chr-cr-403@test.com")
    ac = campaigns_authenticated_client("rt-chr-cr-403")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "pc"},
    )
    assert response.status_code == 403


async def test_create_character_empty_name_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-cr-noname", email="rt-chr-cr-noname@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0003")
    ac = campaigns_authenticated_client("rt-chr-cr-noname")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "  ", "character_type": "pc"},
    )
    assert response.status_code == 422


async def test_create_character_invalid_type_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-cr-badtype", email="rt-chr-cr-badtype@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0004")
    ac = campaigns_authenticated_client("rt-chr-cr-badtype")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "villain"},
    )
    assert response.status_code == 422


async def test_create_character_invalid_slug_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-cr-badslug", email="rt-chr-cr-badslug@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0005")
    ac = campaigns_authenticated_client("rt-chr-cr-badslug")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "Aria Stormwind", "name": "Aria", "character_type": "pc"},
    )
    assert response.status_code == 422


async def test_create_character_reserved_slug_rejected(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-cr-reserved", email="rt-chr-cr-reserved@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0007")
    ac = campaigns_authenticated_client("rt-chr-cr-reserved")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "new", "name": "New Character", "character_type": "npc"},
    )
    assert response.status_code == 422


async def test_create_character_slug_conflict_returns_409(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-cr-conflict", email="rt-chr-cr-conflict@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcc0006")
    await make_character(db, campaign_id=campaign.id, slug="gandalf")
    ac = campaigns_authenticated_client("rt-chr-cr-conflict")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "gandalf", "name": "Gandalf the White", "character_type": "npc"},
    )
    assert response.status_code == 409


async def test_create_character_player_member_can_create(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-cr-plown", email="rt-chr-cr-plown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcc0007")
    player = await make_user(db, supertokens_user_id="rt-chr-cr-player", email="rt-chr-cr-player@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    ac = campaigns_authenticated_client("rt-chr-cr-player")
    response = await ac.post(
        f"/api/v1/campaigns/{campaign.slug}/characters",
        json={"slug": "aria", "name": "Aria", "character_type": "pc"},
    )
    assert response.status_code == 201


# --- Get ---


async def test_get_character_returns_200(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-get-200", email="rt-chr-get-200@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcg0001")
    character = await make_character(db, campaign_id=campaign.id, slug="aria", name="Aria")
    ac = campaigns_authenticated_client("rt-chr-get-200")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}")
    assert response.status_code == 200
    assert response.json()["name"] == "Aria"
    assert response.json()["slug"] == "aria"


async def test_get_character_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-get-own", email="rt-chr-get-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcg0002")
    character = await make_character(db, campaign_id=campaign.id)
    await make_user(db, supertokens_user_id="rt-chr-get-403", email="rt-chr-get-403@test.com")
    ac = campaigns_authenticated_client("rt-chr-get-403")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}")
    assert response.status_code == 403


async def test_get_character_returns_404_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-get-404", email="rt-chr-get-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcg0003")
    ac = campaigns_authenticated_client("rt-chr-get-404")
    response = await ac.get(f"/api/v1/campaigns/{campaign.slug}/characters/nonexistent-character")
    assert response.status_code == 404


async def test_get_character_returns_404_for_wrong_campaign(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-get-iso", email="rt-chr-get-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="rtcga001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="rtcgb001")
    character = await make_character(db, campaign_id=campaign_b.id)
    ac = campaigns_authenticated_client("rt-chr-get-iso")
    response = await ac.get(f"/api/v1/campaigns/{campaign_a.slug}/characters/{character.slug}")
    assert response.status_code == 404


# --- Patch ---


async def test_patch_character_returns_200(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-patch-200", email="rt-chr-patch-200@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcp0001")
    character = await make_character(db, campaign_id=campaign.id, slug="old-char", name="Old")
    ac = campaigns_authenticated_client("rt-chr-patch-200")
    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}",
        json={"name": "New"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New"


async def test_patch_character_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-patch-own", email="rt-chr-patch-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcp0002")
    character = await make_character(db, campaign_id=campaign.id)
    await make_user(db, supertokens_user_id="rt-chr-patch-403", email="rt-chr-patch-403@test.com")
    ac = campaigns_authenticated_client("rt-chr-patch-403")
    response = await ac.patch(
        f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}",
        json={"name": "New"},
    )
    assert response.status_code == 403


# --- Delete ---


async def test_delete_character_returns_204(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-del-204", email="rt-chr-del-204@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcd0001")
    character = await make_character(db, campaign_id=campaign.id)
    ac = campaigns_authenticated_client("rt-chr-del-204")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}")
    assert response.status_code == 204


async def test_delete_character_returns_403_for_non_member(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-del-own", email="rt-chr-del-own@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcd0002")
    character = await make_character(db, campaign_id=campaign.id)
    await make_user(db, supertokens_user_id="rt-chr-del-403", email="rt-chr-del-403@test.com")
    ac = campaigns_authenticated_client("rt-chr-del-403")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}")
    assert response.status_code == 403


async def test_delete_character_returns_404_not_found(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    user = await make_user(db, supertokens_user_id="rt-chr-del-404", email="rt-chr-del-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="rtcd0003")
    ac = campaigns_authenticated_client("rt-chr-del-404")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/nonexistent-character")
    assert response.status_code == 404


async def test_delete_character_player_member_can_delete(
    campaigns_authenticated_client: Callable[[str], AsyncClient],
    db: AsyncSession,
) -> None:
    owner = await make_user(db, supertokens_user_id="rt-chr-del-plown", email="rt-chr-del-plown@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="rtcd0004")
    player = await make_user(db, supertokens_user_id="rt-chr-del-player", email="rt-chr-del-player@test.com")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)
    character = await make_character(db, campaign_id=campaign.id)
    ac = campaigns_authenticated_client("rt-chr-del-player")
    response = await ac.delete(f"/api/v1/campaigns/{campaign.slug}/characters/{character.slug}")
    assert response.status_code == 204
