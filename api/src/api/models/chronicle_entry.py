from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.models.common.campaign_entity import CampaignEntityBase

if TYPE_CHECKING:
    from api.models.user import User


class ChronicleEntry(CampaignEntityBase):
    SLUG_UNIQUE_CONSTRAINT = "uq_chronicle_entries_campaign_slug"

    __tablename__ = "chronicle_entries"
    __table_args__ = (
        Index("ix_chronicle_entries_campaign_occurred_at", "campaign_id", text("occurred_at DESC")),
        UniqueConstraint("campaign_id", "slug", name=SLUG_UNIQUE_CONSTRAINT),
    )

    title: Mapped[str] = mapped_column(String, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    author: Mapped[User | None] = relationship("User", lazy="raise")
