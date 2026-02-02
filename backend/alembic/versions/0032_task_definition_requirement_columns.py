"""Add task_definition requirement columns (from requirements JSON)

Revision ID: 0032_task_req_columns
Revises: 0031_task_codes_event_related
Create Date: 2026-02-02

"""
from alembic import op
import sqlalchemy as sa

revision = "0032_task_req_columns"
down_revision = "0031_task_codes_event_related"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("task_definitions", sa.Column("max_event_tier", sa.String(10), nullable=True))
    op.add_column("task_definitions", sa.Column("min_duration_minutes", sa.Float(), nullable=True))
    op.add_column("task_definitions", sa.Column("max_incidents", sa.Integer(), nullable=True))
    op.add_column("task_definitions", sa.Column("max_penalties", sa.Integer(), nullable=True))
    op.add_column(
        "task_definitions",
        sa.Column("require_night", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "task_definitions",
        sa.Column("require_dynamic_weather", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "task_definitions",
        sa.Column("require_team_event", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "task_definitions",
        sa.Column("require_clean_finish", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "task_definitions",
        sa.Column("allow_non_finish", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("task_definitions", sa.Column("max_position_overall", sa.Integer(), nullable=True))
    op.add_column("task_definitions", sa.Column("min_position_overall", sa.Integer(), nullable=True))
    op.add_column("task_definitions", sa.Column("min_laps_completed", sa.Integer(), nullable=True))
    op.add_column(
        "task_definitions",
        sa.Column("repeatable", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("task_definitions", sa.Column("max_completions", sa.Integer(), nullable=True))
    op.add_column("task_definitions", sa.Column("cooldown_hours", sa.Float(), nullable=True))
    op.add_column("task_definitions", sa.Column("diversity_window_days", sa.Integer(), nullable=True))
    op.add_column("task_definitions", sa.Column("max_same_event_count", sa.Integer(), nullable=True))
    op.add_column("task_definitions", sa.Column("require_event_diversity", sa.Boolean(), nullable=True))
    op.add_column("task_definitions", sa.Column("max_same_signature_count", sa.Integer(), nullable=True))
    op.add_column("task_definitions", sa.Column("signature_cooldown_hours", sa.Float(), nullable=True))
    op.add_column(
        "task_definitions",
        sa.Column("diminishing_returns", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column("task_definitions", sa.Column("diminishing_step", sa.Float(), nullable=True))
    op.add_column("task_definitions", sa.Column("diminishing_floor", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("task_definitions", "diminishing_floor")
    op.drop_column("task_definitions", "diminishing_step")
    op.drop_column("task_definitions", "diminishing_returns")
    op.drop_column("task_definitions", "signature_cooldown_hours")
    op.drop_column("task_definitions", "max_same_signature_count")
    op.drop_column("task_definitions", "require_event_diversity")
    op.drop_column("task_definitions", "max_same_event_count")
    op.drop_column("task_definitions", "diversity_window_days")
    op.drop_column("task_definitions", "cooldown_hours")
    op.drop_column("task_definitions", "max_completions")
    op.drop_column("task_definitions", "repeatable")
    op.drop_column("task_definitions", "min_laps_completed")
    op.drop_column("task_definitions", "min_position_overall")
    op.drop_column("task_definitions", "max_position_overall")
    op.drop_column("task_definitions", "allow_non_finish")
    op.drop_column("task_definitions", "require_clean_finish")
    op.drop_column("task_definitions", "require_team_event")
    op.drop_column("task_definitions", "require_dynamic_weather")
    op.drop_column("task_definitions", "require_night")
    op.drop_column("task_definitions", "max_penalties")
    op.drop_column("task_definitions", "max_incidents")
    op.drop_column("task_definitions", "min_duration_minutes")
    op.drop_column("task_definitions", "max_event_tier")
