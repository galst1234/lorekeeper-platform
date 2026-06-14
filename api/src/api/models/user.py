from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base

if TYPE_CHECKING:
    from api.models.campaign import Campaign
    from api.models.membership import CampaignMember


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    auth_methods: Mapped[list[UserAuthMethod]] = relationship("UserAuthMethod", back_populates="user")
    owned_campaigns: Mapped[list[Campaign]] = relationship("Campaign", back_populates="owner", lazy="raise")
    memberships: Mapped[list[CampaignMember]] = relationship("CampaignMember", back_populates="user", lazy="raise")
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
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


class UserAuthMethod(Base):
    __tablename__ = "user_auth_methods"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_user_auth_methods_user_provider"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String, nullable=False)
    supertokens_user_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    user: Mapped[User] = relationship("User", back_populates="auth_methods")
