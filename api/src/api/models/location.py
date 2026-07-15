from __future__ import annotations

from sqlalchemy import Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from api.models.common.campaign_entity import CampaignEntityBase


class Location(CampaignEntityBase):
    SLUG_UNIQUE_CONSTRAINT = "uq_locations_campaign_slug"

    __tablename__ = "locations"
    __table_args__ = (
        Index("ix_locations_campaign_id", "campaign_id"),
        UniqueConstraint("campaign_id", "slug", name=SLUG_UNIQUE_CONSTRAINT),
    )

    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_key: Mapped[str | None] = mapped_column(String, nullable=True)
