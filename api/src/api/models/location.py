from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

if TYPE_CHECKING:
    from api.models.campaign import Campaign
    from api.models.user import User


class Location(Base):
    SLUG_UNIQUE_CONSTRAINT = "uq_locations_owner_slug"

    __tablename__ = "locations"
    __table_args__ = (
        Index("ix_locations_owner_id", "owner_id"),
        UniqueConstraint("owner_id", "slug", name=SLUG_UNIQUE_CONSTRAINT),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        default=lambda: datetime.now(UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    owner: Mapped[User] = relationship("User", lazy="raise")
    campaign_links: Mapped[list[CampaignLocation]] = relationship(
        "CampaignLocation",
        back_populates="location",
        lazy="raise",
        passive_deletes=True,
    )


class CampaignLocation(Base):
    __tablename__ = "campaign_locations"
    __table_args__ = (Index("ix_campaign_locations_campaign_id", "campaign_id"),)

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, server_default=text("true"), default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        default=lambda: datetime.now(UTC),
    )

    campaign: Mapped[Campaign] = relationship("Campaign", lazy="raise")
    location: Mapped[Location] = relationship("Location", back_populates="campaign_links", lazy="raise")
