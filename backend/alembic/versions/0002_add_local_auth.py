"""add local auth support

Revision ID: 0002
Revises: 0001
Create Date: 2026-03-26

Adiciona password_hash na tabela users e torna ad_object_id nullable
para permitir login local sem LDAP.
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("password_hash", sa.String(256), nullable=True),
        schema="tania",
    )
    op.alter_column(
        "users",
        "ad_object_id",
        nullable=True,
        schema="tania",
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "ad_object_id",
        nullable=False,
        schema="tania",
    )
    op.drop_column("users", "password_hash", schema="tania")
