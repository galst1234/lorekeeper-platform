from sqlalchemy.ext.asyncio import AsyncSession

from api.models import MemberRole
from api.services import items as item_service
from tests.helpers import make_campaign, make_user

# --- tags ---


async def test_create_item_persists_tags(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-tags-cr", email="svc-itm-tags-cr@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itmtag01")
    await item_service.create_item(
        db,
        campaign_id=campaign.id,
        slug="sunblade",
        name="Sunblade",
        description=None,
        tags=["magic", "relic", "weapon"],
    )
    reloaded = await item_service.get_item_by_slug(db, campaign.id, "sunblade", MemberRole.GM)
    assert reloaded is not None
    assert reloaded.tags == ["magic", "relic", "weapon"]


async def test_update_item_replaces_tags(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-tags-up", email="svc-itm-tags-up@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itmtag02")
    item = await item_service.create_item(
        db, campaign_id=campaign.id, slug="sunblade", name="Sunblade", description=None, tags=["magic"]
    )
    await item_service.update_item(db, item, tags=["holy", "sword"])
    reloaded = await item_service.get_item_by_slug(db, campaign.id, "sunblade", MemberRole.GM)
    assert reloaded is not None
    assert reloaded.tags == ["holy", "sword"]


async def test_update_item_omitting_tags_leaves_them(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-itm-tags-om", email="svc-itm-tags-om@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="itmtag03")
    item = await item_service.create_item(
        db, campaign_id=campaign.id, slug="sunblade", name="Sunblade", description=None, tags=["magic"]
    )
    await item_service.update_item(db, item, name="Sunblade Reforged")
    reloaded = await item_service.get_item_by_slug(db, campaign.id, "sunblade", MemberRole.GM)
    assert reloaded is not None
    assert reloaded.tags == ["magic"]
