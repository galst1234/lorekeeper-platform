"""Replace supertokens_user_id on users with user_auth_methods table

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_auth_methods",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("provider", sa.String(), nullable=False),
        sa.Column("supertokens_user_id", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("supertokens_user_id"),
        sa.UniqueConstraint("user_id", "provider", name="uq_user_auth_methods_user_provider"),
    )
    # Migrate existing rows — assume current supertokens_user_id values are emailpassword
    op.execute(
        "INSERT INTO user_auth_methods (user_id, provider, supertokens_user_id) "
        "SELECT id, 'emailpassword', supertokens_user_id FROM users"
    )
    op.drop_constraint("users_supertokens_user_id_key", "users", type_="unique")
    op.drop_column("users", "supertokens_user_id")


def downgrade() -> None:
    op.add_column("users", sa.Column("supertokens_user_id", sa.String(), nullable=True))
    op.execute(
        "UPDATE users u SET supertokens_user_id = m.supertokens_user_id "
        "FROM user_auth_methods m WHERE m.user_id = u.id AND m.provider = 'emailpassword'"
    )
    op.alter_column("users", "supertokens_user_id", nullable=False)
    op.create_unique_constraint("users_supertokens_user_id_key", "users", ["supertokens_user_id"])
    op.drop_table("user_auth_methods")
