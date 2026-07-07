from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import CampaignLocation, Location
from api.services import campaign_locations as campaign_location_service
from api.services.campaign_locations import LocationAlreadyLinkedError, LocationSlugConflictError
from tests.helpers import link_location, make_campaign, make_location, make_user

# --- create_and_link ---


async def test_create_and_link_persists_both_tables(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-cr-link", email="svc-loc-cr-link@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locc0001")
    result = await campaign_location_service.create_and_link(
        db,
        campaign_id=campaign.id,
        owner_id=user.id,
        slug="tavern",
        name="Tavern",
        description="A cozy inn.",
        notes="Session 1",
        is_active=True,
    )
    assert result.slug == "tavern"
    assert result.name == "Tavern"
    assert result.description == "A cozy inn."
    assert result.notes == "Session 1"
    assert result.is_active is True
    assert result.id is not None

    location_row = await db.get(Location, result.id)
    assert location_row is not None
    assert location_row.slug == "tavern"
    assert location_row.owner_id == user.id

    junction = await db.scalar(
        select(CampaignLocation).where(
            CampaignLocation.campaign_id == campaign.id,
            CampaignLocation.location_id == result.id,
        )
    )
    assert junction is not None
    assert junction.is_active is True
    assert junction.notes == "Session 1"


async def test_create_and_link_slug_conflict_raises(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-cr-conflict", email="svc-loc-cr-conflict@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locc0002")
    await make_location(db, owner_id=user.id, slug="tavern", name="Existing Tavern")
    try:
        await campaign_location_service.create_and_link(
            db,
            campaign_id=campaign.id,
            owner_id=user.id,
            slug="tavern",
            name="Another Tavern",
            description=None,
        )
        raise AssertionError("Expected LocationSlugConflictError")
    except LocationSlugConflictError:
        pass


# --- unlink ---


async def test_unlink_removes_junction_preserves_location(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-unlink", email="svc-loc-unlink@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locu0001")
    location = await make_location(db, owner_id=user.id, slug="tavern", name="Tavern")
    await link_location(db, campaign_id=campaign.id, location_id=location.id)
    await campaign_location_service.unlink_campaign_location(
        db,
        campaign_id=campaign.id,
        location_slug=location.slug,
    )
    junction = await db.scalar(
        select(CampaignLocation).where(
            CampaignLocation.campaign_id == campaign.id,
            CampaignLocation.location_id == location.id,
        )
    )
    assert junction is None
    location_row = await db.get(Location, location.id)
    assert location_row is not None
    assert location_row.slug == "tavern"


# --- update_campaign_location ---


async def test_patch_updates_junction_not_canonical(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-patch", email="svc-loc-patch@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locp0001")
    location = await make_location(
        db,
        owner_id=user.id,
        slug="tavern",
        name="Tavern",
        description="Original description",
    )
    await link_location(db, campaign_id=campaign.id, location_id=location.id, is_active=True, notes="Old notes")
    updated = await campaign_location_service.update_campaign_location(
        db,
        campaign_id=campaign.id,
        location_slug=location.slug,
        is_active=False,
        notes="New notes",
    )
    assert updated.is_active is False
    assert updated.notes == "New notes"
    assert updated.name == "Tavern"
    assert updated.description == "Original description"

    location_row = await db.get(Location, location.id)
    assert location_row is not None
    assert location_row.name == "Tavern"
    assert location_row.description == "Original description"

    junction = await db.scalar(
        select(CampaignLocation).where(
            CampaignLocation.campaign_id == campaign.id,
            CampaignLocation.location_id == location.id,
        )
    )
    assert junction is not None
    assert junction.is_active is False
    assert junction.notes == "New notes"


# --- link_location ---


async def test_link_already_linked_raises(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-link-dup", email="svc-loc-link-dup@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="lock0001")
    location = await make_location(db, owner_id=user.id, slug="tavern", name="Tavern")
    await link_location(db, campaign_id=campaign.id, location_id=location.id)
    try:
        await campaign_location_service.link_location(
            db,
            campaign_id=campaign.id,
            location_id=location.id,
        )
        raise AssertionError("Expected LocationAlreadyLinkedError")
    except LocationAlreadyLinkedError:
        pass


# --- list_campaign_locations ---


async def test_list_campaign_locations_empty(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-list-empty", email="svc-loc-list-empty@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locl0001")
    result = await campaign_location_service.list_campaign_locations(db, campaign.id)
    assert result == []


async def test_list_campaign_locations_ordered_by_name(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-list-ord", email="svc-loc-list-ord@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locl0002")
    zebra_tavern = await make_location(db, owner_id=user.id, slug="zebra-tavern", name="Zebra Tavern")
    apple_inn = await make_location(db, owner_id=user.id, slug="apple-inn", name="Apple Inn")
    await link_location(db, campaign_id=campaign.id, location_id=zebra_tavern.id)
    await link_location(db, campaign_id=campaign.id, location_id=apple_inn.id)
    result = await campaign_location_service.list_campaign_locations(db, campaign.id)
    assert result[0].slug == "apple-inn"
    assert result[1].slug == "zebra-tavern"


async def test_list_campaign_locations_excludes_other_campaign(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-list-iso", email="svc-loc-list-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="locla001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="loclb001")
    location = await make_location(db, owner_id=user.id, slug="tavern", name="Tavern")
    await link_location(db, campaign_id=campaign_b.id, location_id=location.id)
    result = await campaign_location_service.list_campaign_locations(db, campaign_a.id)
    assert result == []


async def test_list_campaign_locations_filters_active_only(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-list-active", email="svc-loc-list-active@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locl0003")
    active_location = await make_location(db, owner_id=user.id, slug="tavern", name="Tavern")
    inactive_location = await make_location(db, owner_id=user.id, slug="dungeon", name="Dungeon")
    await link_location(db, campaign_id=campaign.id, location_id=active_location.id, is_active=True)
    await link_location(db, campaign_id=campaign.id, location_id=inactive_location.id, is_active=False)
    result = await campaign_location_service.list_campaign_locations(db, campaign.id, active_only=True)
    assert len(result) == 1
    assert result[0].slug == "tavern"
    assert result[0].is_active is True


# --- get_linked_location_by_slug ---


async def test_get_linked_location_by_slug_found(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-gbs-ok", email="svc-loc-gbs-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locg0001")
    location = await make_location(db, owner_id=user.id, slug="tavern", name="Tavern")
    await link_location(db, campaign_id=campaign.id, location_id=location.id)
    result = await campaign_location_service.get_linked_location_by_slug(db, campaign.id, "tavern")
    assert result is not None
    assert result.slug == "tavern"
    assert result.name == "Tavern"


async def test_get_linked_location_by_slug_not_found_returns_none(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-gbs-404", email="svc-loc-gbs-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locg0002")
    await make_location(db, owner_id=user.id, slug="tavern", name="Tavern")
    result = await campaign_location_service.get_linked_location_by_slug(db, campaign.id, "tavern")
    assert result is None


async def test_get_linked_location_wrong_campaign_returns_none(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-gbs-iso", email="svc-loc-gbs-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="locla002")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="loclb002")
    location = await make_location(db, owner_id=user.id, slug="tavern", name="Tavern")
    await link_location(db, campaign_id=campaign_b.id, location_id=location.id)
    result = await campaign_location_service.get_linked_location_by_slug(db, campaign_a.id, location.slug)
    assert result is None
