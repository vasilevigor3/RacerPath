"""driver games and event game

Revision ID: 0011_driver_games_event_game
Revises: 0010_user_profiles
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0011_driver_games_event_game"
down_revision = "0010_user_profiles"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "drivers",
        sa.Column("sim_games", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )
    op.alter_column("drivers", "sim_games", server_default=None)
    op.add_column("events", sa.Column("game", sa.String(length=60), nullable=True))


def downgrade() -> None:
    op.drop_column("events", "game")
    op.drop_column("drivers", "sim_games")
