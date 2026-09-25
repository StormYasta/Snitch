"""Cache persistente das consultas oficiais pontuais.

Revision ID: a64b8f27c901
Revises: 7fd7e1b0e0a9
"""
from alembic import op
import sqlalchemy as sa

revision = "a64b8f27c901"
down_revision = "7fd7e1b0e0a9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "official_cache",
        sa.Column("cache_key", sa.String(length=200), primary_key=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_official_cache_source", "official_cache", ["source"])
    if op.get_bind().dialect.name == "postgresql":
        op.execute("ALTER TABLE public.official_cache ENABLE ROW LEVEL SECURITY")
        op.execute("REVOKE ALL ON public.official_cache FROM anon, authenticated, service_role")


def downgrade() -> None:
    op.drop_index("ix_official_cache_source", table_name="official_cache")
    op.drop_table("official_cache")
