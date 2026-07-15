from __future__ import annotations

import enum

from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from api.models.common.campaign_entity import CampaignEntityBase


class CharacterType(enum.StrEnum):
    PC = "pc"
    NPC = "npc"


class Character(CampaignEntityBase):
    SLUG_UNIQUE_CONSTRAINT = "uq_characters_campaign_slug"

    __tablename__ = "characters"
    __table_args__ = (
        Index("ix_characters_campaign_id", "campaign_id"),
        UniqueConstraint("campaign_id", "slug", name=SLUG_UNIQUE_CONSTRAINT),
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    character_type: Mapped[CharacterType] = mapped_column(
        SqlEnum(
            CharacterType,
            name="character_type",
            values_callable=lambda types: [enum_member.value for enum_member in types],
        ),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_key: Mapped[str | None] = mapped_column(String, nullable=True)
