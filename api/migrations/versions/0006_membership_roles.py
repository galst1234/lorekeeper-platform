"""membership roles

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-28

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE TYPE member_role AS ENUM ('gm', 'player')")
    op.add_column(
        "campaign_members",
        sa.Column(
            "role",
            sa.Enum("gm", "player", name="member_role", create_type=False),
            nullable=True,
        ),
    )
    op.execute("UPDATE campaign_members SET role = 'player'")
    op.execute("""
        INSERT INTO campaign_members (campaign_id, user_id, joined_at, role)
        SELECT id, owner_id, created_at, 'gm'
        FROM campaigns
        ON CONFLICT (campaign_id, user_id) DO UPDATE SET role = 'gm'
    """)
    op.alter_column(
        "campaign_members",
        "role",
        existing_type=sa.Enum("gm", "player", name="member_role", create_type=False),
        nullable=False,
    )


def downgrade() -> None:
    op.execute("DELETE FROM campaign_members WHERE role = 'gm'")
    op.drop_column("campaign_members", "role")
    op.execute("DROP TYPE member_role")
