"""task completion v2 fields

Revision ID: 0009_task_completion_v2
Revises: 0008_driver_user_link
Create Date: 2026-01-28
"""

from alembic import op
import sqlalchemy as sa

revision = "0009_task_completion_v2"
down_revision = "0008_driver_user_link"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("task_completions", sa.Column("event_signature", sa.String(length=64), nullable=True))
    op.add_column(
        "task_completions",
        sa.Column("score_multiplier", sa.Float(), nullable=False, server_default="1.0"),
    )
    op.alter_column("task_completions", "score_multiplier", server_default=None)


def downgrade() -> None:
    op.drop_column("task_completions", "score_multiplier")
    op.drop_column("task_completions", "event_signature")
