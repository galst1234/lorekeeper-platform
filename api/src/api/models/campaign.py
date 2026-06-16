from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

if TYPE_CHECKING:
    from api.models.membership import CampaignMember
    from api.models.user import User

SLUG_ID_UNIQUE_CONSTRAINT = "uq_campaigns_slug_id"


class Campaign(Base):
    __tablename__ = "campaigns"
    __table_args__ = (
        UniqueConstraint("slug_id", name=SLUG_ID_UNIQUE_CONSTRAINT),
        Index("ix_campaigns_owner_id_created_at", "owner_id", "created_at"),
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
    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    slug_label: Mapped[str] = mapped_column(String, nullable=False)
    slug_id: Mapped[str] = mapped_column(String(8), nullable=False, index=True)
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
    invite_code: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)

    owner: Mapped[User] = relationship("User", back_populates="owned_campaigns", lazy="raise")
    members: Mapped[list[CampaignMember]] = relationship(
        "CampaignMember", back_populates="campaign", lazy="raise", passive_deletes=True
    )

    @property
    def slug(self) -> str:
        return f"{self.slug_label}-{self.slug_id}"
