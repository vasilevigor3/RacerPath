"""event fields + classification inputs

Revision ID: 0003_event_classification_inputs
Revises: 0002_raw_events
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_event_classification_inputs"
down_revision = "0002_raw_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "events",
        sa.Column("session_list", sa.JSON(), nullable=False, server_default=sa.text("'[]'::jsonb")),
    )
    op.add_column(
        "events",
        sa.Column("team_size_min", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "events",
        sa.Column("team_size_max", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "events",
        sa.Column("rolling_start", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "events",
        sa.Column("pit_rules", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")),
    )
    op.add_column(
        "events",
        sa.Column("time_acceleration", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "events",
        sa.Column("surface_type", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "events",
        sa.Column("track_type", sa.String(length=20), nullable=True),
    )

    op.add_column(
        "classifications",
        sa.Column("inputs_hash", sa.String(length=64), nullable=False, server_default=""),
    )
    op.add_column(
        "classifications",
        sa.Column(
            "inputs_snapshot", sa.JSON(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
    )


def downgrade() -> None:
    op.drop_column("classifications", "inputs_snapshot")
    op.drop_column("classifications", "inputs_hash")

    op.drop_column("events", "track_type")
    op.drop_column("events", "surface_type")
    op.drop_column("events", "time_acceleration")
    op.drop_column("events", "pit_rules")
    op.drop_column("events", "rolling_start")
    op.drop_column("events", "team_size_max")
    op.drop_column("events", "team_size_min")
    op.drop_column("events", "session_list")