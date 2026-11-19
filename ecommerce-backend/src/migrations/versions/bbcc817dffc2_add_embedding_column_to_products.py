"""add embedding column to products

Revision ID: bbcc817dffc2
Revises: 8ae726f3d786
Create Date: 2026-09-29 11:41:56.833218

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import pgvector


# revision identifiers, used by Alembic.
revision: str = "bbcc817dffc2"
down_revision: Union[str, Sequence[str], None] = "8ae726f3d786"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with pgvector when available, or float[] fallback."""
    conn = op.get_bind()
    has_pgvector = conn.execute(
        sa.text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
    ).scalar()

    if has_pgvector:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        op.add_column(
            "products",
            sa.Column(
                "embedding",
                pgvector.sqlalchemy.vector.VECTOR(dim=1536),
                nullable=True,
            ),
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_products_embedding ON products "
            "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);"
        )
    else:
        op.add_column(
            "products",
            sa.Column("embedding", sa.ARRAY(sa.Float()), nullable=True),
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_products_embedding;")
    op.drop_column("products", "embedding")
