from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import MemberRole
from api.services import locations as location_service
from api.services.locations import LocationSlugConflictError
from api.storage import LocalDiskStorage
from tests.helpers import make_campaign, make_location, make_user

# --- list_locations ---


async def test_list_locations_empty(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-list-empty", email="svc-loc-list-empty@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locl0001")
    result = await location_service.list_locations(db, campaign.id, MemberRole.GM)
    assert result == []


async def test_list_locations_returns_all(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-list-all", email="svc-loc-list-all@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locl0002")
    tavern = await make_location(db, campaign_id=campaign.id, slug="tavern", name="Tavern")
    dungeon = await make_location(db, campaign_id=campaign.id, slug="dungeon", name="Dungeon")
    result = await location_service.list_locations(db, campaign.id, MemberRole.GM)
    ids = [location.id for location in result]
    assert tavern.id in ids
    assert dungeon.id in ids


async def test_list_locations_ordered_by_name(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-list-ord", email="svc-loc-list-ord@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locl0003")
    zebra_tavern = await make_location(db, campaign_id=campaign.id, slug="zebra-tavern", name="Zebra Tavern")
    apple_inn = await make_location(db, campaign_id=campaign.id, slug="apple-inn", name="Apple Inn")
    result = await location_service.list_locations(db, campaign.id, MemberRole.GM)
    assert result[0].id == apple_inn.id
    assert result[1].id == zebra_tavern.id


async def test_list_locations_excludes_other_campaign(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-list-iso", email="svc-loc-list-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="locla001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="loclb001")
    await make_location(db, campaign_id=campaign_b.id, name="Other")
    result = await location_service.list_locations(db, campaign_a.id, MemberRole.GM)
    assert result == []


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
    )
    assert location.slug == "moonlit-tavern"
    assert location.name == "Moonlit Tavern"
    assert location.description == "A cozy inn."
    assert location.campaign_id == campaign.id
    assert location.id is not None
    assert location.restricted is False


async def test_create_location_restricted_true_persists(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-cr-restr", email="svc-loc-cr-restr@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locc0004")
    location = await location_service.create_location(
        db,
        campaign_id=campaign.id,
        slug="secret",
        name="Secret Room",
        description=None,
        restricted=True,
    )
    assert location.restricted is True


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
    result = await location_service.get_location_by_slug(db, campaign.id, "tavern", MemberRole.GM)
    assert result is not None
    assert result.slug == "tavern"


async def test_get_location_by_slug_not_found(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-gbs-404", email="svc-loc-gbs-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locs0002")
    result = await location_service.get_location_by_slug(db, campaign.id, "nonexistent", MemberRole.GM)
    assert result is None


async def test_get_location_by_slug_wrong_campaign_returns_none(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-gbs-iso", email="svc-loc-gbs-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="locga001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="locgb001")
    await make_location(db, campaign_id=campaign_b.id, slug="tavern")
    result = await location_service.get_location_by_slug(db, campaign_a.id, "tavern", MemberRole.GM)
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


async def test_update_location_missing_fields_unchanged(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-upd-miss", email="svc-loc-upd-miss@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locp0004")
    location = await make_location(
        db,
        campaign_id=campaign.id,
        name="Keep Me",
        description="Also keep",
    )
    updated = await location_service.update_location(db, location, description="Changed")
    assert updated.name == "Keep Me"
    assert updated.description == "Changed"


async def test_update_location_restricted_toggles(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-upd-restr", email="svc-loc-upd-restr@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locp0005")
    location = await make_location(db, campaign_id=campaign.id, restricted=False)
    updated = await location_service.update_location(db, location, restricted=True)
    assert updated.restricted is True


# --- visibility ---


async def test_list_locations_excludes_restricted_for_player(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-vis-list-p", email="svc-loc-vis-list-p@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locv0001")
    await make_location(db, campaign_id=campaign.id, slug="public", name="Public")
    await make_location(db, campaign_id=campaign.id, slug="secret", name="Secret", restricted=True)
    result = await location_service.list_locations(db, campaign.id, MemberRole.PLAYER)
    assert len(result) == 1
    assert result[0].slug == "public"


async def test_list_locations_includes_restricted_for_gm(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-vis-list-g", email="svc-loc-vis-list-g@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locv0002")
    secret = await make_location(db, campaign_id=campaign.id, slug="secret", name="Secret", restricted=True)
    result = await location_service.list_locations(db, campaign.id, MemberRole.GM)
    assert secret.id in [location.id for location in result]


async def test_get_location_by_slug_restricted_returns_none_for_player(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-vis-get-p", email="svc-loc-vis-get-p@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locv0003")
    await make_location(db, campaign_id=campaign.id, slug="secret", restricted=True)
    result = await location_service.get_location_by_slug(db, campaign.id, "secret", MemberRole.PLAYER)
    assert result is None


async def test_get_location_by_slug_restricted_returns_value_for_gm(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-vis-get-g", email="svc-loc-vis-get-g@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locv0004")
    await make_location(db, campaign_id=campaign.id, slug="secret", restricted=True)
    result = await location_service.get_location_by_slug(db, campaign.id, "secret", MemberRole.GM)
    assert result is not None


# --- delete_location ---


async def test_delete_location_removes_record(db: AsyncSession, tmp_path: Path) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-del-ok", email="svc-loc-del-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locd0001")
    location = await make_location(db, campaign_id=campaign.id)
    location_slug = location.slug
    image_storage = LocalDiskStorage(root=str(tmp_path))
    await location_service.delete_location(db, location, image_storage)
    result = await location_service.get_location_by_slug(db, campaign.id, location_slug, MemberRole.GM)
    assert result is None


async def test_delete_location_removes_image_file(db: AsyncSession, tmp_path: Path) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-del-img", email="svc-loc-del-img@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="locd0002")
    location = await make_location(db, campaign_id=campaign.id)
    image_storage = LocalDiskStorage(root=str(tmp_path))
    key = await image_storage.save(b"location-bytes", "image/png")
    location.image_key = key
    await db.commit()
    await location_service.delete_location(db, location, image_storage)
    assert not (tmp_path / key).exists()


async def test_set_location_image_sets_key(db: AsyncSession, tmp_path: Path) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-img-set", email="svc-loc-img-set@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="loci0001")
    location = await make_location(db, campaign_id=campaign.id)
    image_storage = LocalDiskStorage(root=str(tmp_path))
    updated = await location_service.set_location_image(db, location, "new-key.png", image_storage)
    assert updated.image_key == "new-key.png"


async def test_set_location_image_deletes_old_file_after_replacing(db: AsyncSession, tmp_path: Path) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-img-replace", email="svc-loc-img-replace@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="loci0002")
    location = await make_location(db, campaign_id=campaign.id)
    image_storage = LocalDiskStorage(root=str(tmp_path))
    old_key = await image_storage.save(b"old-bytes", "image/png")
    location.image_key = old_key
    await db.commit()
    await location_service.set_location_image(db, location, "new-key.png", image_storage)
    assert not (tmp_path / old_key).exists()


async def test_clear_location_image_clears_key_and_deletes_file(db: AsyncSession, tmp_path: Path) -> None:
    user = await make_user(db, supertokens_user_id="svc-loc-img-clear", email="svc-loc-img-clear@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="loci0003")
    location = await make_location(db, campaign_id=campaign.id)
    image_storage = LocalDiskStorage(root=str(tmp_path))
    key = await image_storage.save(b"location-bytes", "image/png")
    location.image_key = key
    await db.commit()
    updated = await location_service.clear_location_image(db, location, image_storage)
    assert updated.image_key is None
    assert not (tmp_path / key).exists()
