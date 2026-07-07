import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.services import locations as location_service
from api.services.locations import LocationSlugConflictError
from tests.helpers import make_campaign, make_location, make_user

# --- list_locations ---


async def test_list_locations_empty(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-list-empty", email="svc-loc-list-empty@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locl0001")
    result = await location_service.list_locations(db, campaign.id)
    assert result == []


async def test_list_locations_returns_all(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-list-all", email="svc-loc-list-all@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locl0002")
    tavern = await make_location(db, campaign_id=campaign.id, slug="tavern", name="Tavern")
    dungeon = await make_location(db, campaign_id=campaign.id, slug="dungeon", name="Dungeon")
    result = await location_service.list_locations(db, campaign.id)
    ids = [location.id for location in result]
    assert tavern.id in ids
    assert dungeon.id in ids


async def test_list_locations_ordered_by_name(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-list-ord", email="svc-loc-list-ord@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locl0003")
    zebra_tavern = await make_location(db, campaign_id=campaign.id, slug="zebra-tavern", name="Zebra Tavern")
    apple_inn = await make_location(db, campaign_id=campaign.id, slug="apple-inn", name="Apple Inn")
    result = await location_service.list_locations(db, campaign.id)
    assert result[0].id == apple_inn.id
    assert result[1].id == zebra_tavern.id


async def test_list_locations_excludes_other_campaign(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-list-iso", email="svc-loc-list-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="locla001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="loclb001")
    await make_location(db, campaign_id=campaign_b.id, name="Other")
    result = await location_service.list_locations(db, campaign_a.id)
    assert result == []


async def test_list_locations_filters_active_only(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-list-active", email="svc-loc-list-active@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locl0004")
    await make_location(db, campaign_id=campaign.id, slug="tavern", name="Tavern", is_active=True)
    await make_location(db, campaign_id=campaign.id, slug="dungeon", name="Dungeon", is_active=False)
    result = await location_service.list_locations(db, campaign.id, active_only=True)
    assert len(result) == 1
    assert result[0].slug == "tavern"
    assert result[0].is_active is True


# --- create_location ---


async def test_create_location_persists(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-cr-ok", email="svc-loc-cr-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locc0001")
    location = await location_service.create_location(
        db,
        campaign_id=campaign.id,
        slug="moonlit-tavern",
        name="Moonlit Tavern",
        description="A cozy inn.",
        is_active=True,
        notes="Session 1",
    )
    assert location.slug == "moonlit-tavern"
    assert location.name == "Moonlit Tavern"
    assert location.description == "A cozy inn."
    assert location.is_active is True
    assert location.notes == "Session 1"
    assert location.campaign_id == campaign.id
    assert location.id is not None


async def test_create_location_no_description(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-cr-nodesc", email="svc-loc-cr-nodesc@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locc0002")
    location = await location_service.create_location(
        db,
        campaign_id=campaign.id,
        slug="plains",
        name="Open Plains",
        description=None,
    )
    assert location.description is None


async def test_create_location_slug_conflict_raises(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-cr-conflict", email="svc-loc-cr-conflict@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locc0003")
    await location_service.create_location(
        db,
        campaign_id=campaign.id,
        slug="tavern",
        name="Tavern",
        description=None,
    )
    with pytest.raises(LocationSlugConflictError):
        await location_service.create_location(
            db,
            campaign_id=campaign.id,
            slug="tavern",
            name="Another Tavern",
            description=None,
        )


async def test_create_location_same_slug_different_campaigns_ok(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-cr-xcamp", email="svc-loc-cr-xcamp@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="locca001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="loccb001")
    await location_service.create_location(
        db,
        campaign_id=campaign_a.id,
        slug="tavern",
        name="Tavern",
        description=None,
    )
    location = await location_service.create_location(
        db,
        campaign_id=campaign_b.id,
        slug="tavern",
        name="Tavern",
        description=None,
    )
    assert location.slug == "tavern"


# --- get_location_by_slug ---


async def test_get_location_by_slug_found(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-gbs-ok", email="svc-loc-gbs-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locs0001")
    await make_location(db, campaign_id=campaign.id, slug="tavern")
    result = await location_service.get_location_by_slug(db, campaign.id, "tavern")
    assert result is not None
    assert result.slug == "tavern"


async def test_get_location_by_slug_not_found(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-gbs-404", email="svc-loc-gbs-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locs0002")
    result = await location_service.get_location_by_slug(db, campaign.id, "nonexistent")
    assert result is None


async def test_get_location_by_slug_wrong_campaign_returns_none(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-gbs-iso", email="svc-loc-gbs-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="locga001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="locgb001")
    await make_location(db, campaign_id=campaign_b.id, slug="tavern")
    result = await location_service.get_location_by_slug(db, campaign_a.id, "tavern")
    assert result is None


# --- update_location ---


async def test_update_location_name(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-upd-name", email="svc-loc-upd-name@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locp0001")
    location = await make_location(db, campaign_id=campaign.id, name="Old Name")
    updated = await location_service.update_location(db, location, name="New Name")
    assert updated.name == "New Name"


async def test_update_location_description(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-upd-desc", email="svc-loc-upd-desc@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locp0002")
    location = await make_location(db, campaign_id=campaign.id, description="Old description")
    updated = await location_service.update_location(db, location, description="New description")
    assert updated.description == "New description"


async def test_update_location_is_active_and_notes(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-upd-active", email="svc-loc-upd-active@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locp0003")
    location = await make_location(db, campaign_id=campaign.id, is_active=True, notes="Old notes")
    updated = await location_service.update_location(db, location, is_active=False, notes="New notes")
    assert updated.is_active is False
    assert updated.notes == "New notes"


async def test_update_location_missing_fields_unchanged(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-upd-miss", email="svc-loc-upd-miss@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locp0004")
    location = await make_location(
        db,
        campaign_id=campaign.id,
        name="Keep Me",
        description="Also keep",
        is_active=True,
        notes="Keep notes",
    )
    updated = await location_service.update_location(db, location, notes="Changed")
    assert updated.name == "Keep Me"
    assert updated.description == "Also keep"
    assert updated.is_active is True
    assert updated.notes == "Changed"


# --- delete_location ---


async def test_delete_location_removes_record(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-del-ok", email="svc-loc-del-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locd0001")
    location = await make_location(db, campaign_id=campaign.id)
    location_slug = location.slug
    await location_service.delete_location(db, location)
    result = await location_service.get_location_by_slug(db, campaign.id, location_slug)
    assert result is None
