"""add product image_url and unique cart per user

Revision ID: c1a2b3d4e5f6
Revises: bbcc817dffc2
Create Date: 2026-11-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c1a2b3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "bbcc817dffc2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "products",
        sa.Column("image_url", sa.String(length=500), nullable=True),
    )
    op.alter_column(
        "products",
        "version",
        existing_type=sa.Integer(),
        server_default=sa.text("1"),
    )

    # Keep the oldest cart per user before enforcing uniqueness. This is
    # destructive only for duplicate carts created by the old race condition.
    op.execute(
        """
        DELETE FROM carts a
        USING carts b
        WHERE a.user_id = b.user_id
          AND (a.created_at, a.id) > (b.created_at, b.id)
        """
    )
    op.create_unique_constraint("uq_carts_user_id", "carts", ["user_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("uq_carts_user_id", "carts", type_="unique")
    op.alter_column(
        "products",
        "version",
        existing_type=sa.Integer(),
        server_default=sa.text("0"),
    )
    op.drop_column("products", "image_url")
