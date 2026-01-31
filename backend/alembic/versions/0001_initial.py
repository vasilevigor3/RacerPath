"""initial schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "drivers",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("primary_discipline", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "events",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("start_time_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("schedule_type", sa.String(length=20), nullable=False),
        sa.Column("event_type", sa.String(length=30), nullable=False),
        sa.Column("format_type", sa.String(length=30), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("grid_size_expected", sa.Integer(), nullable=False),
        sa.Column("class_count", sa.Integer(), nullable=False),
        sa.Column("car_class_list", sa.JSON(), nullable=False),
        sa.Column("damage_model", sa.String(length=20), nullable=False),
        sa.Column("penalties", sa.String(length=20), nullable=False),
        sa.Column("fuel_usage", sa.String(length=20), nullable=False),
        sa.Column("tire_wear", sa.String(length=20), nullable=False),
        sa.Column("weather", sa.String(length=20), nullable=False),
        sa.Column("night", sa.Boolean(), nullable=False),
        sa.Column("stewarding", sa.String(length=20), nullable=False),
        sa.Column("team_event", sa.Boolean(), nullable=False),
        sa.Column("license_requirement", sa.String(length=20), nullable=False),
        sa.Column("official_event", sa.Boolean(), nullable=False),
        sa.Column("assists_allowed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "classifications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("event_id", sa.String(length=36), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("event_tier", sa.String(length=10), nullable=False),
        sa.Column("tier_label", sa.String(length=40), nullable=False),
        sa.Column("difficulty_score", sa.Float(), nullable=False),
        sa.Column("seriousness_score", sa.Float(), nullable=False),
        sa.Column("realism_score", sa.Float(), nullable=False),
        sa.Column("discipline_compatibility", sa.JSON(), nullable=False),
        sa.Column("caps_applied", sa.JSON(), nullable=False),
        sa.Column("classification_version", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "participations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("driver_id", sa.String(length=36), sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("event_id", sa.String(length=36), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("discipline", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("position_overall", sa.Integer(), nullable=True),
        sa.Column("position_class", sa.Integer(), nullable=True),
        sa.Column("laps_completed", sa.Integer(), nullable=False),
        sa.Column("incidents_count", sa.Integer(), nullable=False),
        sa.Column("penalties_count", sa.Integer(), nullable=False),
        sa.Column("pace_delta", sa.Float(), nullable=True),
        sa.Column("consistency_score", sa.Float(), nullable=True),
        sa.Column("raw_metrics", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "incidents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("participation_id", sa.String(length=36), sa.ForeignKey("participations.id"), nullable=False),
        sa.Column("incident_type", sa.String(length=40), nullable=False),
        sa.Column("severity", sa.Integer(), nullable=False),
        sa.Column("lap", sa.Integer(), nullable=True),
        sa.Column("timestamp_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("description", sa.String(length=240), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "task_definitions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("discipline", sa.String(length=20), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("requirements", sa.JSON(), nullable=False),
        sa.Column("min_event_tier", sa.String(length=10), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("code", name="uq_task_definitions_code"),
    )

    op.create_table(
        "task_completions",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("driver_id", sa.String(length=36), sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("task_id", sa.String(length=36), sa.ForeignKey("task_definitions.id"), nullable=False),
        sa.Column("participation_id", sa.String(length=36), sa.ForeignKey("participations.id"), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("notes", sa.String(length=240), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "crs_history",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("driver_id", sa.String(length=36), sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("discipline", sa.String(length=20), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("inputs", sa.JSON(), nullable=False),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("driver_id", sa.String(length=36), sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("discipline", sa.String(length=20), nullable=False),
        sa.Column("readiness_status", sa.String(length=20), nullable=False),
        sa.Column("summary", sa.String(length=300), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("recommendations")
    op.drop_table("crs_history")
    op.drop_table("task_completions")
    op.drop_table("task_definitions")
    op.drop_table("incidents")
    op.drop_table("participations")
    op.drop_table("classifications")
    op.drop_table("events")
    op.drop_table("drivers")