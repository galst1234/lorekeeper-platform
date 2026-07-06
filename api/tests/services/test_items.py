from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from api.services import items as item_service
from api.services.items import ItemSlugConflictError
from api.storage import LocalDiskStorage
from tests.helpers import make_campaign, make_item, make_user

# --- list_items ---


async def test_list_items_empty(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-list-empty", email="svc-itm-list-empty@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itml0001")
    result = await item_service.list_items(db, campaign.id)
    assert result == []


async def test_list_items_returns_all(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-list-all", email="svc-itm-list-all@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itml0002")
    sword = await make_item(db, campaign_id=campaign.id, slug="sword", name="Sword")
    shield = await make_item(db, campaign_id=campaign.id, slug="shield", name="Shield")
    result = await item_service.list_items(db, campaign.id)
    ids = [item.id for item in result]
    assert sword.id in ids
    assert shield.id in ids


async def test_list_items_ordered_by_name(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-list-ord", email="svc-itm-list-ord@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itml0003")
    zebra_axe = await make_item(db, campaign_id=campaign.id, slug="zebra-axe", name="Zebra Axe")
    apple_bow = await make_item(db, campaign_id=campaign.id, slug="apple-bow", name="Apple Bow")
    result = await item_service.list_items(db, campaign.id)
    assert result[0].id == apple_bow.id
    assert result[1].id == zebra_axe.id


async def test_list_items_excludes_other_campaign(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-list-iso", email="svc-itm-list-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="itmla001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="itmlb001")
    await make_item(db, campaign_id=campaign_b.id, name="Other")
    result = await item_service.list_items(db, campaign_a.id)
    assert result == []


# --- create_item ---


async def test_create_item_persists(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-cr-ok", email="svc-itm-cr-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itmc0001")
    item = await item_service.create_item(
        db,
        campaign_id=campaign.id,
        slug="moonblade",
        name="Moonblade",
        description="A blade that glows under moonlight.",
    )
    assert item.slug == "moonblade"
    assert item.name == "Moonblade"
    assert item.description == "A blade that glows under moonlight."
    assert item.campaign_id == campaign.id
    assert item.id is not None


async def test_create_item_no_description(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-cr-nodesc", email="svc-itm-cr-nodesc@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itmc0002")
    item = await item_service.create_item(
        db,
        campaign_id=campaign.id,
        slug="plain-rock",
        name="Plain Rock",
        description=None,
    )
    assert item.description is None


async def test_create_item_slug_conflict_raises(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-cr-conflict", email="svc-itm-cr-conflict@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itmc0003")
    await item_service.create_item(
        db,
        campaign_id=campaign.id,
        slug="ring-of-power",
        name="Ring of Power",
        description=None,
    )
    try:
        await item_service.create_item(
            db,
            campaign_id=campaign.id,
            slug="ring-of-power",
            name="Another Ring",
            description=None,
        )
        raise AssertionError("Expected ItemSlugConflictError")
    except ItemSlugConflictError:
        pass


async def test_create_item_same_slug_different_campaigns_ok(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-cr-xcamp", email="svc-itm-cr-xcamp@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="itmca001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="itmcb001")
    await item_service.create_item(
        db,
        campaign_id=campaign_a.id,
        slug="ring-of-power",
        name="Ring of Power",
        description=None,
    )
    item = await item_service.create_item(
        db,
        campaign_id=campaign_b.id,
        slug="ring-of-power",
        name="Ring of Power",
        description=None,
    )
    assert item.slug == "ring-of-power"


# --- get_item_by_slug ---


async def test_get_item_by_slug_found(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-gbs-ok", email="svc-itm-gbs-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itms0001")
    await make_item(db, campaign_id=campaign.id, slug="lantern")
    result = await item_service.get_item_by_slug(db, campaign.id, "lantern")
    assert result is not None
    assert result.slug == "lantern"


async def test_get_item_by_slug_not_found(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-gbs-404", email="svc-itm-gbs-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itms0002")
    result = await item_service.get_item_by_slug(db, campaign.id, "nonexistent")
    assert result is None


async def test_get_item_by_slug_wrong_campaign_returns_none(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-gbs-iso", email="svc-itm-gbs-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="itmsa001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="itmsb001")
    await make_item(db, campaign_id=campaign_b.id, slug="lantern")
    result = await item_service.get_item_by_slug(db, campaign_a.id, "lantern")
    assert result is None


# --- update_item ---


async def test_update_item_name(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-upd-name", email="svc-itm-upd-name@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itmu0001")
    item = await make_item(db, campaign_id=campaign.id, name="Old Name")
    updated = await item_service.update_item(db, item, name="New Name")
    assert updated.name == "New Name"


async def test_update_item_description(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-upd-desc", email="svc-itm-upd-desc@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itmu0002")
    item = await make_item(db, campaign_id=campaign.id, description="Old description")
    updated = await item_service.update_item(db, item, description="New description")
    assert updated.description == "New description"


async def test_update_item_missing_fields_unchanged(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-upd-miss", email="svc-itm-upd-miss@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itmu0003")
    item = await make_item(db, campaign_id=campaign.id, name="Keep Me", description="Also keep")
    updated = await item_service.update_item(db, item, description="Changed")
    assert updated.name == "Keep Me"
    assert updated.description == "Changed"


# --- delete_item ---


async def test_delete_item_removes_record(db: AsyncSession, tmp_path: Path) -> None:
    user = await make_user(db, supertokens_user_id="svc-item-del-ok", email="svc-item-del-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itmd0001")
    item = await make_item(db, campaign_id=campaign.id)
    item_slug = item.slug
    storage = LocalDiskStorage(root=str(tmp_path))
    await item_service.delete_item(db, item, storage)
    result = await item_service.get_item_by_slug(db, campaign.id, item_slug)
    assert result is None


async def test_delete_item_removes_image_file(db: AsyncSession, tmp_path: Path) -> None:
    user = await make_user(db, supertokens_user_id="svc-item-del-img", email="svc-item-del-img@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itmd0002")
    item = await make_item(db, campaign_id=campaign.id)
    storage = LocalDiskStorage(root=str(tmp_path))
    key = await storage.save(b"item-bytes", "image/png")
    item.image_key = key
    await db.commit()
    await item_service.delete_item(db, item, storage)
    assert not (tmp_path / key).exists()


async def test_set_item_image_sets_key(db: AsyncSession, tmp_path: Path) -> None:
    user = await make_user(db, supertokens_user_id="svc-item-img-set", email="svc-item-img-set@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itmi0001")
    item = await make_item(db, campaign_id=campaign.id)
    storage = LocalDiskStorage(root=str(tmp_path))
    updated = await item_service.set_item_image(db, item, "new-key.png", storage)
    assert updated.image_key == "new-key.png"


async def test_set_item_image_deletes_old_file_after_replacing(db: AsyncSession, tmp_path: Path) -> None:
    user = await make_user(db, supertokens_user_id="svc-item-img-replace", email="svc-item-img-replace@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itmi0002")
    item = await make_item(db, campaign_id=campaign.id)
    storage = LocalDiskStorage(root=str(tmp_path))
    old_key = await storage.save(b"old-bytes", "image/png")
    item.image_key = old_key
    await db.commit()
    await item_service.set_item_image(db, item, "new-key.png", storage)
    assert not (tmp_path / old_key).exists()


async def test_clear_item_image_clears_key_and_deletes_file(db: AsyncSession, tmp_path: Path) -> None:
    user = await make_user(db, supertokens_user_id="svc-item-img-clear", email="svc-item-img-clear@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itmi0003")
    item = await make_item(db, campaign_id=campaign.id)
    storage = LocalDiskStorage(root=str(tmp_path))
    key = await storage.save(b"item-bytes", "image/png")
    item.image_key = key
    await db.commit()
    updated = await item_service.clear_item_image(db, item, storage)
    assert updated.image_key is None
    assert not (tmp_path / key).exists()
