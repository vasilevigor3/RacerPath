"""user email and password

Revision ID: 0012_user_email_password
Revises: 0011_driver_games_event_game
Create Date: 2026-01-29
"""

from alembic import op
import sqlalchemy as sa

revision = "0012_user_email_password"
down_revision = "0011_driver_games_event_game"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("email", sa.String(length=200), nullable=True))
    op.add_column("users", sa.Column("password_hash", sa.String(length=200), nullable=True))
    op.create_index("uq_users_email", "users", ["email"], unique=True)


def downgrade() -> None:
    op.drop_index("uq_users_email", table_name="users")
    op.drop_column("users", "password_hash")
    op.drop_column("users", "email")
