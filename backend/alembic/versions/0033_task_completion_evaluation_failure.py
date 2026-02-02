"""Add task_completion evaluation_failed_at and evaluation_failure_reasons

Revision ID: 0033_eval_failure
Revises: 0032_task_req_columns
Create Date: 2026-01-30

"""
from alembic import op
import sqlalchemy as sa

revision = "0033_eval_failure"
down_revision = "0032_task_req_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "task_completions",
        sa.Column("evaluation_failed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "task_completions",
        sa.Column("evaluation_failure_reasons", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("task_completions", "evaluation_failure_reasons")
    op.drop_column("task_completions", "evaluation_failed_at")
