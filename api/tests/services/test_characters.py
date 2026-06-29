import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from api.models import CharacterType
from api.services import characters as character_service
from tests.helpers import make_campaign, make_character, make_user

# --- list_characters ---


async def test_list_characters_empty(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-list-empty", email="svc-chr-list-empty@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrl0001")
    result = await character_service.list_characters(db, campaign.id)
    assert result == []


async def test_list_characters_returns_all(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-list-all", email="svc-chr-list-all@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrl0002")
    pc = await make_character(db, campaign_id=campaign.id, name="Aria", character_type=CharacterType.PC)
    npc = await make_character(db, campaign_id=campaign.id, name="Innkeeper", character_type=CharacterType.NPC)
    result = await character_service.list_characters(db, campaign.id)
    ids = [c.id for c in result]
    assert pc.id in ids
    assert npc.id in ids


async def test_list_characters_filters_by_type(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-list-flt", email="svc-chr-list-flt@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrl0003")
    pc = await make_character(db, campaign_id=campaign.id, name="Aria", character_type=CharacterType.PC)
    await make_character(db, campaign_id=campaign.id, name="Innkeeper", character_type=CharacterType.NPC)
    result = await character_service.list_characters(db, campaign.id, character_type=CharacterType.PC)
    assert len(result) == 1
    assert result[0].id == pc.id


async def test_list_characters_ordered_by_created_at(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-list-ord", email="svc-chr-list-ord@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrl0004")
    first = await make_character(db, campaign_id=campaign.id, name="First")
    second = await make_character(db, campaign_id=campaign.id, name="Second")
    result = await character_service.list_characters(db, campaign.id)
    assert result[0].id == first.id
    assert result[1].id == second.id


async def test_list_characters_excludes_other_campaign(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-list-iso", email="svc-chr-list-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="chrla001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="chrlb001")
    await make_character(db, campaign_id=campaign_b.id, name="Other")
    result = await character_service.list_characters(db, campaign_a.id)
    assert result == []


# --- create_character ---


async def test_create_character_persists(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-cr-ok", email="svc-chr-cr-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrc0001")
    character = await character_service.create_character(
        db,
        campaign_id=campaign.id,
        name="Aria Stormwind",
        character_type=CharacterType.PC,
        description="A half-elf ranger.",
    )
    assert character.name == "Aria Stormwind"
    assert character.character_type == CharacterType.PC
    assert character.description == "A half-elf ranger."
    assert character.campaign_id == campaign.id
    assert character.id is not None


async def test_create_character_no_description(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-cr-nodesc", email="svc-chr-cr-nodesc@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrc0002")
    character = await character_service.create_character(
        db,
        campaign_id=campaign.id,
        name="Nameless",
        character_type=CharacterType.NPC,
        description=None,
    )
    assert character.description is None


# --- get_character ---


async def test_get_character_found(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-get-ok", email="svc-chr-get-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrg0001")
    character = await make_character(db, campaign_id=campaign.id)
    result = await character_service.get_character(db, campaign.id, character.id)
    assert result is not None
    assert result.id == character.id


async def test_get_character_not_found(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-get-404", email="svc-chr-get-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrg0002")
    result = await character_service.get_character(db, campaign.id, uuid.uuid4())
    assert result is None


async def test_get_character_wrong_campaign_returns_none(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-get-iso", email="svc-chr-get-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="chrga001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="chrgb001")
    character = await make_character(db, campaign_id=campaign_b.id)
    result = await character_service.get_character(db, campaign_a.id, character.id)
    assert result is None


# --- update_character ---


async def test_update_character_name(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-upd-name", email="svc-chr-upd-name@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chru0001")
    character = await make_character(db, campaign_id=campaign.id, name="Old Name")
    updated = await character_service.update_character(db, character, name="New Name")
    assert updated.name == "New Name"
    assert updated.character_type == CharacterType.PC


async def test_update_character_type(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-upd-type", email="svc-chr-upd-type@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chru0002")
    character = await make_character(db, campaign_id=campaign.id, character_type=CharacterType.PC)
    updated = await character_service.update_character(db, character, character_type=CharacterType.NPC)
    assert updated.character_type == CharacterType.NPC


async def test_update_character_missing_fields_unchanged(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-upd-miss", email="svc-chr-upd-miss@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chru0003")
    character = await make_character(db, campaign_id=campaign.id, name="Keep Me", description="Also keep")
    updated = await character_service.update_character(db, character, character_type=CharacterType.NPC)
    assert updated.name == "Keep Me"
    assert updated.description == "Also keep"


# --- delete_character ---


async def test_delete_character_removes_record(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-del-ok", email="svc-chr-del-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrd0001")
    character = await make_character(db, campaign_id=campaign.id)
    character_id = character.id
    await character_service.delete_character(db, character)
    result = await character_service.get_character(db, campaign.id, character_id)
    assert result is None
