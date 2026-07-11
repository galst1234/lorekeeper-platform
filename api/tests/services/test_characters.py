from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from api.models import CharacterType, MemberRole
from api.services import characters as character_service
from api.services.characters import CharacterSlugConflictError
from api.storage import LocalDiskStorage
from tests.helpers import make_campaign, make_character, make_user

# --- list_characters ---


async def test_list_characters_empty(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-list-empty", email="svc-chr-list-empty@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrl0001")
    result = await character_service.list_characters(db, campaign.id, MemberRole.GM)
    assert result == []


async def test_list_characters_returns_all(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-list-all", email="svc-chr-list-all@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrl0002")
    pc = await make_character(db, campaign_id=campaign.id, slug="aria", name="Aria", character_type=CharacterType.PC)
    npc = await make_character(
        db, campaign_id=campaign.id, slug="innkeeper", name="Innkeeper", character_type=CharacterType.NPC
    )
    result = await character_service.list_characters(db, campaign.id, MemberRole.GM)
    ids = [character.id for character in result]
    assert pc.id in ids
    assert npc.id in ids


async def test_list_characters_filters_by_type(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-list-flt", email="svc-chr-list-flt@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrl0003")
    pc = await make_character(db, campaign_id=campaign.id, slug="aria", name="Aria", character_type=CharacterType.PC)
    await make_character(
        db, campaign_id=campaign.id, slug="innkeeper", name="Innkeeper", character_type=CharacterType.NPC
    )
    result = await character_service.list_characters(db, campaign.id, MemberRole.GM, character_type=CharacterType.PC)
    assert len(result) == 1
    assert result[0].id == pc.id


async def test_list_characters_ordered_by_created_at(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-list-ord", email="svc-chr-list-ord@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrl0004")
    first = await make_character(db, campaign_id=campaign.id, slug="first", name="First")
    second = await make_character(db, campaign_id=campaign.id, slug="second", name="Second")
    result = await character_service.list_characters(db, campaign.id, MemberRole.GM)
    assert result[0].id == first.id
    assert result[1].id == second.id


async def test_list_characters_excludes_other_campaign(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-list-iso", email="svc-chr-list-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="chrla001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="chrlb001")
    await make_character(db, campaign_id=campaign_b.id, name="Other")
    result = await character_service.list_characters(db, campaign_a.id, MemberRole.GM)
    assert result == []


# --- create_character ---


async def test_create_character_persists(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-cr-ok", email="svc-chr-cr-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrc0001")
    character = await character_service.create_character(
        db,
        campaign_id=campaign.id,
        slug="aria-stormwind",
        name="Aria Stormwind",
        character_type=CharacterType.PC,
        description="A half-elf ranger.",
    )
    assert character.slug == "aria-stormwind"
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
        slug="nameless",
        name="Nameless",
        character_type=CharacterType.NPC,
        description=None,
    )
    assert character.description is None


async def test_create_character_slug_conflict_raises(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-cr-conflict", email="svc-chr-cr-conflict@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrc0003")
    await character_service.create_character(
        db,
        campaign_id=campaign.id,
        slug="gandalf",
        name="Gandalf the Grey",
        character_type=CharacterType.NPC,
        description=None,
    )
    try:
        await character_service.create_character(
            db,
            campaign_id=campaign.id,
            slug="gandalf",
            name="Gandalf the White",
            character_type=CharacterType.NPC,
            description=None,
        )
        raise AssertionError("Expected CharacterSlugConflictError")
    except CharacterSlugConflictError:
        pass


async def test_create_character_same_slug_different_campaigns_ok(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-cr-xcamp", email="svc-chr-cr-xcamp@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="chrca001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="chrcb001")
    await character_service.create_character(
        db,
        campaign_id=campaign_a.id,
        slug="gandalf",
        name="Gandalf",
        character_type=CharacterType.NPC,
        description=None,
    )
    character = await character_service.create_character(
        db,
        campaign_id=campaign_b.id,
        slug="gandalf",
        name="Gandalf",
        character_type=CharacterType.NPC,
        description=None,
    )
    assert character.slug == "gandalf"


# --- get_character_by_slug ---


async def test_get_character_by_slug_found(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-gbs-ok", email="svc-chr-gbs-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrs0001")
    await make_character(db, campaign_id=campaign.id, slug="aria")
    result = await character_service.get_character_by_slug(db, campaign.id, "aria", MemberRole.GM)
    assert result is not None
    assert result.slug == "aria"


async def test_get_character_by_slug_not_found(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-gbs-404", email="svc-chr-gbs-404@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrs0002")
    result = await character_service.get_character_by_slug(db, campaign.id, "nonexistent", MemberRole.GM)
    assert result is None


async def test_get_character_by_slug_wrong_campaign_returns_none(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-gbs-iso", email="svc-chr-gbs-iso@test.com")
    campaign_a = await make_campaign(db, owner_id=user.id, slug_id="chrsa001")
    campaign_b = await make_campaign(db, owner_id=user.id, slug_id="chrsb001")
    await make_character(db, campaign_id=campaign_b.id, slug="aria")
    result = await character_service.get_character_by_slug(db, campaign_a.id, "aria", MemberRole.GM)
    assert result is None


# --- visibility ---


async def test_list_characters_excludes_restricted_for_player(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-vis-list", email="svc-chr-vis-list@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrv0001")
    visible = await make_character(db, campaign_id=campaign.id, slug="visible")
    await make_character(db, campaign_id=campaign.id, slug="secret", restricted=True)
    result = await character_service.list_characters(db, campaign.id, MemberRole.PLAYER)
    assert [character.id for character in result] == [visible.id]


async def test_list_characters_includes_restricted_for_gm(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-vis-list-gm", email="svc-chr-vis-list-gm@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrv0002")
    secret = await make_character(db, campaign_id=campaign.id, slug="secret", restricted=True)
    result = await character_service.list_characters(db, campaign.id, MemberRole.GM)
    assert secret.id in [character.id for character in result]


async def test_get_character_by_slug_restricted_returns_none_for_player(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-vis-get", email="svc-chr-vis-get@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrv0003")
    await make_character(db, campaign_id=campaign.id, slug="secret", restricted=True)
    result = await character_service.get_character_by_slug(db, campaign.id, "secret", MemberRole.PLAYER)
    assert result is None


async def test_get_character_by_slug_restricted_returns_value_for_gm(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-vis-get-gm", email="svc-chr-vis-get-gm@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrv0004")
    await make_character(db, campaign_id=campaign.id, slug="secret", restricted=True)
    result = await character_service.get_character_by_slug(db, campaign.id, "secret", MemberRole.GM)
    assert result is not None


async def test_create_character_restricted_defaults_false(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-vis-cr-default", email="svc-chr-vis-cr-default@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrv0005")
    character = await character_service.create_character(
        db, campaign_id=campaign.id, slug="aria", name="Aria", character_type=CharacterType.PC, description=None
    )
    assert character.restricted is False


async def test_create_character_restricted_true_persists(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-vis-cr-true", email="svc-chr-vis-cr-true@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrv0006")
    character = await character_service.create_character(
        db,
        campaign_id=campaign.id,
        slug="aria",
        name="Aria",
        character_type=CharacterType.PC,
        description=None,
        restricted=True,
    )
    assert character.restricted is True


async def test_update_character_restricted_toggles(db: AsyncSession) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-vis-upd", email="svc-chr-vis-upd@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrv0007")
    character = await make_character(db, campaign_id=campaign.id, restricted=False)
    updated = await character_service.update_character(db, character, restricted=True)
    assert updated.restricted is True


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


async def test_delete_character_removes_record(db: AsyncSession, tmp_path: Path) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-del-ok", email="svc-chr-del-ok@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrd0001")
    character = await make_character(db, campaign_id=campaign.id)
    character_slug = character.slug
    image_storage = LocalDiskStorage(root=str(tmp_path))
    await character_service.delete_character(db, character, image_storage)
    result = await character_service.get_character_by_slug(db, campaign.id, character_slug, MemberRole.GM)
    assert result is None


async def test_delete_character_removes_image_file(db: AsyncSession, tmp_path: Path) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-del-img", email="svc-chr-del-img@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chrd0002")
    character = await make_character(db, campaign_id=campaign.id)
    image_storage = LocalDiskStorage(root=str(tmp_path))
    key = await image_storage.save(b"portrait-bytes", "image/jpeg")
    character.image_key = key
    await db.commit()
    await character_service.delete_character(db, character, image_storage)
    assert not (tmp_path / key).exists()


# --- set_character_image ---


async def test_set_character_image_sets_key(db: AsyncSession, tmp_path: Path) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-img-set", email="svc-chr-img-set@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chri0001")
    character = await make_character(db, campaign_id=campaign.id)
    image_storage = LocalDiskStorage(root=str(tmp_path))
    updated = await character_service.set_character_image(db, character, "new-key.jpg", image_storage)
    assert updated.image_key == "new-key.jpg"


async def test_set_character_image_deletes_old_file_after_replacing(db: AsyncSession, tmp_path: Path) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-img-replace", email="svc-chr-img-replace@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chri0002")
    character = await make_character(db, campaign_id=campaign.id)
    image_storage = LocalDiskStorage(root=str(tmp_path))
    old_key = await image_storage.save(b"old-bytes", "image/jpeg")
    character.image_key = old_key
    await db.commit()
    await character_service.set_character_image(db, character, "new-key.jpg", image_storage)
    assert not (tmp_path / old_key).exists()


# --- clear_character_image ---


async def test_clear_character_image_clears_key_and_deletes_file(db: AsyncSession, tmp_path: Path) -> None:
    user = await make_user(db, supertokens_user_id="svc-chr-img-clear", email="svc-chr-img-clear@test.com")
    campaign = await make_campaign(db, owner_id=user.id, slug_id="chri0003")
    character = await make_character(db, campaign_id=campaign.id)
    image_storage = LocalDiskStorage(root=str(tmp_path))
    key = await image_storage.save(b"portrait-bytes", "image/jpeg")
    character.image_key = key
    await db.commit()
    updated = await character_service.clear_character_image(db, character, image_storage)
    assert updated.image_key is None
    assert not (tmp_path / key).exists()
