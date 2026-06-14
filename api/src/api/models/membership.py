from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

if TYPE_CHECKING:
    from api.models.campaign import Campaign
    from api.models.user import User


class CampaignMember(Base):
    __tablename__ = "campaign_members"
    __table_args__ = (Index("ix_campaign_members_user_id", "user_id"),)

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        default=lambda: datetime.now(UTC),
    )

    campaign: Mapped[Campaign] = relationship("Campaign", back_populates="members", lazy="raise")
    user: Mapped[User] = relationship("User", back_populates="memberships", lazy="raise")
