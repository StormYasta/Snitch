"""Expandir descrições de status oficiais para TEXT.

Revision ID: 7fd7e1b0e0a9
Revises: 30d164bc1533
"""
from alembic import op
import sqlalchemy as sa

revision = "7fd7e1b0e0a9"
down_revision = "30d164bc1533"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # batch_alter_table também funciona nos testes SQLite da CI.
    with op.batch_alter_table("deputados") as batch:
        batch.alter_column(
            "descricao_status",
            existing_type=sa.String(length=255),
            type_=sa.Text(),
            existing_nullable=True,
        )
    with op.batch_alter_table("deputado_historico") as batch:
        batch.alter_column(
            "descricao_status",
            existing_type=sa.String(length=255),
            type_=sa.Text(),
            existing_nullable=True,
        )


def downgrade() -> None:
    connection = op.get_bind()
    for table in ("deputados", "deputado_historico"):
        count = connection.execute(
            sa.text(f"SELECT COUNT(*) FROM {table} WHERE length(descricao_status) > 255")
        ).scalar_one()
        if count:
            raise RuntimeError(
                f"Não é seguro reduzir {table}.descricao_status: "
                f"{count} registros excedem 255 caracteres."
            )
    with op.batch_alter_table("deputado_historico") as batch:
        batch.alter_column(
            "descricao_status",
            existing_type=sa.Text(),
            type_=sa.String(length=255),
            existing_nullable=True,
        )
    with op.batch_alter_table("deputados") as batch:
        batch.alter_column(
            "descricao_status",
            existing_type=sa.Text(),
            type_=sa.String(length=255),
            existing_nullable=True,
        )
