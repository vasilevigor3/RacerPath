"""auth users + audit logs

Revision ID: 0005_auth_audit
Revises: 0004_license_ladders
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_auth_audit"
down_revision = "0004_license_ladders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("api_key_hash", sa.String(length=64), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("actor_user_id", sa.String(length=36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("actor_role", sa.String(length=20), nullable=True),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("path", sa.String(length=200), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("users")
