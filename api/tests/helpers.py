import re
import uuid
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from api.models import (
    Campaign,
    CampaignMember,
    Character,
    CharacterType,
    ChronicleEntry,
    Item,
    Location,
    MemberRole,
    User,
    UserAuthMethod,
)


async def make_user(
    db: AsyncSession,
    *,
    supertokens_user_id: str,
    email: str,
    display_name: str = "Test User",
) -> User:
    user = User(email=email, display_name=display_name)
    db.add(user)
    await db.flush()
    db.add(UserAuthMethod(user_id=user.id, provider="emailpassword", supertokens_user_id=supertokens_user_id))
    await db.flush()
    return user


async def make_campaign(
    db: AsyncSession,
    *,
    owner_id: uuid.UUID,
    name: str = "Test Campaign",
    slug_label: str = "test-campaign",
    slug_id: str = "aabbccdd",
    description: str | None = None,
    invite_code: str | None = None,
    created_at: datetime | None = None,
) -> Campaign:
    campaign = Campaign(
        owner_id=owner_id,
        name=name,
        description=description,
        slug_label=slug_label,
        slug_id=slug_id,
        invite_code=invite_code,
    )
    if created_at is not None:
        campaign.created_at = created_at
    db.add(campaign)
    await db.flush()
    gm_member = CampaignMember(campaign_id=campaign.id, user_id=owner_id, role=MemberRole.GM)
    db.add(gm_member)
    await db.flush()
    return campaign


async def make_character(
    db: AsyncSession,
    *,
    campaign_id: uuid.UUID,
    name: str = "Test Character",
    slug: str | None = None,
    character_type: CharacterType = CharacterType.PC,
    description: str | None = None,
    restricted: bool = False,
) -> Character:
    if slug is None:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    character = Character(
        campaign_id=campaign_id,
        slug=slug,
        name=name,
        character_type=character_type,
        description=description,
        restricted=restricted,
    )
    db.add(character)
    await db.flush()
    return character


async def make_item(
    db: AsyncSession,
    *,
    campaign_id: uuid.UUID,
    name: str = "Test Item",
    slug: str | None = None,
    description: str | None = None,
    restricted: bool = False,
) -> Item:
    if slug is None:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    item = Item(
        campaign_id=campaign_id,
        slug=slug,
        name=name,
        description=description,
        restricted=restricted,
    )
    db.add(item)
    await db.flush()
    return item


async def make_chronicle_entry(
    db: AsyncSession,
    *,
    campaign_id: uuid.UUID,
    title: str = "Test Entry",
    slug: str | None = None,
    occurred_at: datetime | None = None,
    body: str | None = None,
    author_id: uuid.UUID | None = None,
    restricted: bool = False,
) -> ChronicleEntry:
    if slug is None:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if occurred_at is None:
        occurred_at = datetime.now(UTC)
    entry = ChronicleEntry(
        campaign_id=campaign_id,
        slug=slug,
        title=title,
        occurred_at=occurred_at,
        body=body,
        author_id=author_id,
        restricted=restricted,
    )
    db.add(entry)
    await db.flush()
    return entry


async def make_location(
    db: AsyncSession,
    *,
    campaign_id: uuid.UUID,
    name: str = "Tavern",
    slug: str | None = None,
    description: str | None = None,
    restricted: bool = False,
) -> Location:
    if slug is None:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    location = Location(
        campaign_id=campaign_id,
        slug=slug,
        name=name,
        description=description,
        restricted=restricted,
    )
    db.add(location)
    await db.flush()
    return location


async def make_member(
    db: AsyncSession,
    *,
    campaign_id: uuid.UUID,
    user_id: uuid.UUID,
    role: MemberRole = MemberRole.PLAYER,
) -> CampaignMember:
    member = CampaignMember(campaign_id=campaign_id, user_id=user_id, role=role)
    db.add(member)
    await db.flush()
    return member


# --- In-memory builders (never persisted) ---
#
# For solitary router tests: the object is only read by the route/mocked
# service layer in-process, never queried back from a database. Use the
# `make_*` factories above instead when a test needs the row to actually
# exist for a real query (sociable service tests, e.g.).


def build_campaign(
    *,
    name: str = "Test Campaign",
    description: str | None = None,
    slug_label: str = "test-campaign",
    slug_id: str = "aabbccdd",
    invite_code: str | None = None,
) -> Campaign:
    now = datetime.now(UTC)
    return Campaign(
        id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        name=name,
        description=description,
        slug_label=slug_label,
        slug_id=slug_id,
        invite_code=invite_code,
        created_at=now,
        updated_at=now,
    )


def build_member(
    *,
    campaign_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    role: MemberRole = MemberRole.GM,
) -> CampaignMember:
    return CampaignMember(
        campaign_id=campaign_id or uuid.uuid4(),
        user_id=user_id or uuid.uuid4(),
        role=role,
        joined_at=datetime.now(UTC),
    )


def build_user(*, email: str = "test@example.com", display_name: str | None = "Test User") -> User:
    now = datetime.now(UTC)
    return User(id=uuid.uuid4(), email=email, display_name=display_name, created_at=now, updated_at=now)


def build_character(
    *,
    campaign_id: uuid.UUID | None = None,
    name: str = "Test Character",
    slug: str | None = None,
    character_type: CharacterType = CharacterType.PC,
    description: str | None = None,
    restricted: bool = False,
    image_key: str | None = None,
    tags: list[str] | None = None,
) -> Character:
    if slug is None:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    now = datetime.now(UTC)
    return Character(
        id=uuid.uuid4(),
        campaign_id=campaign_id or uuid.uuid4(),
        slug=slug,
        name=name,
        character_type=character_type,
        description=description,
        restricted=restricted,
        image_key=image_key,
        tags=tags if tags is not None else [],
        created_at=now,
        updated_at=now,
    )


def build_item(
    *,
    campaign_id: uuid.UUID | None = None,
    name: str = "Test Item",
    slug: str | None = None,
    description: str | None = None,
    restricted: bool = False,
    image_key: str | None = None,
    tags: list[str] | None = None,
) -> Item:
    if slug is None:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    now = datetime.now(UTC)
    return Item(
        id=uuid.uuid4(),
        campaign_id=campaign_id or uuid.uuid4(),
        slug=slug,
        name=name,
        description=description,
        restricted=restricted,
        image_key=image_key,
        tags=tags if tags is not None else [],
        created_at=now,
        updated_at=now,
    )


def build_location(
    *,
    campaign_id: uuid.UUID | None = None,
    name: str = "Test Location",
    slug: str | None = None,
    description: str | None = None,
    restricted: bool = False,
    image_key: str | None = None,
    tags: list[str] | None = None,
) -> Location:
    if slug is None:
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    now = datetime.now(UTC)
    return Location(
        id=uuid.uuid4(),
        campaign_id=campaign_id or uuid.uuid4(),
        slug=slug,
        name=name,
        description=description,
        restricted=restricted,
        image_key=image_key,
        tags=tags if tags is not None else [],
        created_at=now,
        updated_at=now,
    )


def build_chronicle_entry(
    *,
    campaign_id: uuid.UUID | None = None,
    title: str = "Test Entry",
    slug: str | None = None,
    occurred_at: datetime | None = None,
    body: str | None = None,
    author_id: uuid.UUID | None = None,
    author: User | None = None,
    restricted: bool = False,
    tags: list[str] | None = None,
) -> ChronicleEntry:
    if slug is None:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if occurred_at is None:
        occurred_at = datetime.now(UTC)
    now = datetime.now(UTC)
    return ChronicleEntry(
        id=uuid.uuid4(),
        campaign_id=campaign_id or uuid.uuid4(),
        slug=slug,
        title=title,
        occurred_at=occurred_at,
        body=body,
        author_id=author_id,
        author=author,
        restricted=restricted,
        tags=tags if tags is not None else [],
        created_at=now,
        updated_at=now,
    )
