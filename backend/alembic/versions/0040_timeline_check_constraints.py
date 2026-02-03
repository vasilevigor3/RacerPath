"""Add timeline check constraints: Event (created_at <= start <= finished); Participation (created_at < started_at <= finished_at).

Revision ID: 0040_timeline_checks
Revises: 0039_penalty_drop_part_id
Create Date: 2026-02-03

"""
from alembic import op

revision = "0040_timeline_checks"
down_revision = "0039_penalty_drop_part_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_events_created_at_lte_start_time_utc",
        "events",
        "start_time_utc IS NULL OR created_at <= start_time_utc",
    )
    op.create_check_constraint(
        "ck_events_start_lte_finished",
        "events",
        "finished_time_utc IS NULL OR start_time_utc IS NULL OR start_time_utc <= finished_time_utc",
    )
    op.create_check_constraint(
        "ck_participations_created_lt_started",
        "participations",
        "started_at IS NULL OR created_at < started_at",
    )
    op.create_check_constraint(
        "ck_participations_started_lte_finished",
        "participations",
        "finished_at IS NULL OR started_at IS NULL OR started_at <= finished_at",
    )


def downgrade() -> None:
    op.drop_constraint("ck_participations_started_lte_finished", "participations", type_="check")
    op.drop_constraint("ck_participations_created_lt_started", "participations", type_="check")
    op.drop_constraint("ck_events_start_lte_finished", "events", type_="check")
    op.drop_constraint("ck_events_created_at_lte_start_time_utc", "events", type_="check")
