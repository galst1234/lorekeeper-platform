from sqlalchemy.ext.asyncio import AsyncSession

from api.services import campaigns as campaign_service
from tests.helpers import make_campaign, make_member, make_user

# --- generate_invite ---


async def test_generate_invite_sets_code(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="inv-gen-ok", email="inv-gen-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="invgen01")
    assert campaign.invite_code is None

    updated = await campaign_service.generate_invite(db, campaign)

    assert updated.invite_code is not None
    assert len(updated.invite_code) > 0


async def test_generate_invite_idempotent(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="inv-gen-idem", email="inv-gen-idem@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="invgid01", invite_code="existing1")

    updated = await campaign_service.generate_invite(db, campaign)

    assert updated.invite_code == "existing1"


# --- revoke_invite ---


async def test_revoke_invite_clears_code(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="inv-rev-ok", email="inv-rev-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="invrev01", invite_code="clearme1")

    await campaign_service.revoke_invite(db, campaign)

    refreshed = await campaign_service.get_campaign_by_slug(db, "test-campaign-invrev01")
    assert refreshed is not None
    assert refreshed.invite_code is None


async def test_revoke_invite_no_code_is_noop(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="inv-rev-noop", email="inv-rev-noop@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="invrvn01")

    await campaign_service.revoke_invite(db, campaign)  # should not raise

    refreshed = await campaign_service.get_campaign_by_slug(db, "test-campaign-invrvn01")
    assert refreshed is not None
    assert refreshed.invite_code is None


# --- join_campaign ---


async def test_join_campaign_adds_member(db: AsyncSession) -> None:
    owner = await make_user(db, supertokens_user_id="inv-join-own", email="inv-join-own@test.com")
    player = await make_user(db, supertokens_user_id="inv-join-ply", email="inv-join-ply@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="injoin01", invite_code="joincode")

    result = await campaign_service.join_campaign(db, campaign, player.id, "joincode")

    assert result is True
    members = await campaign_service.list_members(db, campaign.id)
    assert any(m.user_id == player.id for m in members)


async def test_join_campaign_idempotent(db: AsyncSession) -> None:
    owner = await make_user(db, supertokens_user_id="inv-join-idem", email="inv-join-idem@test.com")
    player = await make_user(db, supertokens_user_id="inv-join-iply", email="inv-join-iply@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="injoid01", invite_code="joincode")

    await campaign_service.join_campaign(db, campaign, player.id, "joincode")
    await campaign_service.join_campaign(db, campaign, player.id, "joincode")

    members = await campaign_service.list_members(db, campaign.id)
    assert len([m for m in members if m.user_id == player.id]) == 1


async def test_join_campaign_owner_is_noop(db: AsyncSession) -> None:
    owner = await make_user(db, supertokens_user_id="inv-join-own2", email="inv-join-own2@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="injown01", invite_code="joincode")

    result = await campaign_service.join_campaign(db, campaign, owner.id, "joincode")

    assert result is True
    members = await campaign_service.list_members(db, campaign.id)
    assert not any(m.user_id == owner.id for m in members)


async def test_join_campaign_revoked_code_returns_false(db: AsyncSession) -> None:
    owner = await make_user(db, supertokens_user_id="inv-join-rev", email="inv-join-rev@test.com")
    player = await make_user(db, supertokens_user_id="inv-join-rply", email="inv-join-rply@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="injrev01", invite_code="revoked1")
    await campaign_service.revoke_invite(db, campaign)

    result = await campaign_service.join_campaign(db, campaign, player.id, "revoked1")

    assert result is False
    members = await campaign_service.list_members(db, campaign.id)
    assert not any(m.user_id == player.id for m in members)


# --- list_campaigns with membership ---


async def test_list_campaigns_includes_member_campaigns(db: AsyncSession) -> None:
    owner = await make_user(db, supertokens_user_id="inv-lst-own", email="inv-lst-own@test.com")
    player = await make_user(db, supertokens_user_id="inv-lst-ply", email="inv-lst-ply@test.com")
    campaign = await make_campaign(db, owner_id=owner.id, slug_id="invlst01")
    await make_member(db, campaign_id=campaign.id, user_id=player.id)

    result = await campaign_service.list_campaigns(db, player.id)

    assert len(result) == 1
    assert result[0].campaign.id == campaign.id
    assert result[0].role == "player"


async def test_list_campaigns_gm_role_for_owned(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="inv-lst-gm", email="inv-lst-gm@test.com")
    await make_campaign(db, owner_id=user.id, slug_id="invlgm01")

    result = await campaign_service.list_campaigns(db, user.id)

    assert len(result) == 1
    assert result[0].role == "gm"


async def test_list_campaigns_excludes_owned_from_player_list(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="inv-lst-dup", email="inv-lst-dup@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="invldup1")
    await make_member(db, campaign_id=campaign.id, user_id=user.id)

    result = await campaign_service.list_campaigns(db, user.id)

    roles = [r.role for r in result]
    assert roles.count("gm") == 1
    assert "player" not in roles
