"""Backfill participation.classification_id from event's classification

Revision ID: 0026_backfill_part_class
Revises: 0025_part_class_id
Create Date: 2026-01-30

"""
from alembic import op

revision = "0026_backfill_part_class"
down_revision = "0025_part_class_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Set classification_id for participations where it's null, using the event's latest classification
    op.execute(
        """
        UPDATE participations p
        SET classification_id = (
            SELECT c.id
            FROM classifications c
            WHERE c.event_id = p.event_id
            ORDER BY c.created_at DESC NULLS LAST
            LIMIT 1
        )
        WHERE p.classification_id IS NULL
        AND EXISTS (
            SELECT 1 FROM classifications c2 WHERE c2.event_id = p.event_id
        )
        """
    )


def downgrade() -> None:
    # No automatic rollback: we don't clear classification_id (could break CRS)
    pass
