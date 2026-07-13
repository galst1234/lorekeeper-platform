from sqlalchemy.ext.asyncio import AsyncSession

from api.models import MemberRole
from api.services import items as item_service
from api.services import tags as tag_service
from tests.helpers import make_campaign, make_user


async def test_non_gm_does_not_see_tags_only_on_restricted_entities(db: AsyncSession) -> None:
    owner = await make_user(db, supertokens_user_id="tags-owner", email="tags-owner@example.com")
    campaign = await make_campaign(db, owner_id=owner.id)
    await item_service.create_item(
        db,
        campaign_id=campaign.id,
        slug="public",
        name="Public",
        description=None,
        restricted=False,
        tags=["public-tag"],
    )
    await item_service.create_item(
        db,
        campaign_id=campaign.id,
        slug="secret",
        name="Secret",
        description=None,
        restricted=True,
        tags=["secret-tag"],
    )

    gm_tags = await tag_service.list_campaign_tags(db, campaign.id, MemberRole.GM)
    player_tags = await tag_service.list_campaign_tags(db, campaign.id, MemberRole.PLAYER)

    assert "secret-tag" in gm_tags
    assert "public-tag" in gm_tags
    assert player_tags == ["public-tag"]
