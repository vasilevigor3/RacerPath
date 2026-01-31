"""unique constraints for classifications and participations

Revision ID: 0014_unique_constraints
Revises: 0013_add_states
Create Date: 2026-01-30
"""

from alembic import op

revision = "0014_unique_constraints"
down_revision = "0013_add_states"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_classifications_event_id",
        "classifications",
        ["event_id"],
    )
    op.create_unique_constraint(
        "uq_participations_driver_event",
        "participations",
        ["driver_id", "event_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_participations_driver_event", "participations", type_="unique")
    op.drop_constraint("uq_classifications_event_id", "classifications", type_="unique")
