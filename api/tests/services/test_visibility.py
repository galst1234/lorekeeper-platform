from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import Character, MemberRole
from api.services.common.visibility import apply_visibility_filter
from tests.helpers import make_campaign, make_character, make_user


async def test_apply_visibility_filter_gm_sees_restricted_rows(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-vis-gm", email="svc-vis-gm@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="visg0001")
    restricted = await make_character(db, campaign_id=campaign.id, slug="secret-npc")
    restricted.restricted = True
    await db.commit()

    query = apply_visibility_filter(
        select(Character).where(Character.campaign_id == campaign.id), Character, MemberRole.GM
    )
    result = list(await db.scalars(query))

    assert restricted.id in [character.id for character in result]


async def test_apply_visibility_filter_player_excludes_restricted_rows(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-vis-player", email="svc-vis-player@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="visp0001")
    visible = await make_character(db, campaign_id=campaign.id, slug="visible-npc")
    restricted = await make_character(db, campaign_id=campaign.id, slug="secret-npc")
    restricted.restricted = True
    await db.commit()

    query = apply_visibility_filter(
        select(Character).where(Character.campaign_id == campaign.id), Character, MemberRole.PLAYER
    )
    result = list(await db.scalars(query))
    ids = [character.id for character in result]

    assert visible.id in ids
    assert restricted.id not in ids
