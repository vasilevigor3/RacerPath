"""event and participation states

Revision ID: 0013_add_states
Revises: 0012_user_email_password
Create Date: 2026-01-30
"""

from alembic import op
import sqlalchemy as sa

revision = "0013_add_states"
down_revision = "0012_user_email_password"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    participation_state_enum = sa.Enum(
        "registered",
        "withdrawn",
        "started",
        "completed",
        name="participation_state_enum",
    )
    event_status_enum = sa.Enum(
        "draft",
        "scheduled",
        "live",
        "completed",
        "cancelled",
        name="event_status_enum",
    )

    participation_state_enum.create(bind, checkfirst=True)
    event_status_enum.create(bind, checkfirst=True)

    op.add_column(
        "participations",
        sa.Column(
            "participation_state",
            sa.Enum(
                "registered",
                "withdrawn",
                "started",
                "completed",
                name="participation_state_enum",
            ),
            nullable=False,
            server_default=sa.text("'registered'"),
        ),
    )

    op.add_column(
        "events",
        sa.Column(
            "event_status",
            sa.Enum(
                "draft",
                "scheduled",
                "live",
                "completed",
                "cancelled",
                name="event_status_enum",
            ),
            nullable=False,
            server_default=sa.text("'scheduled'"),
        ),
    )


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_column("events", "event_status")
    op.drop_column("participations", "participation_state")

    sa.Enum(name="event_status_enum").drop(bind, checkfirst=True)
    sa.Enum(name="participation_state_enum").drop(bind, checkfirst=True)
