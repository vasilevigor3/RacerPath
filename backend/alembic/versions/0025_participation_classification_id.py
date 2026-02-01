"""Add participation.classification_id FK to classifications

Revision ID: 0025_part_class_id
Revises: 0024_ver_num_64
Create Date: 2026-02-01

"""
from alembic import op
import sqlalchemy as sa

revision = "0025_part_class_id"
down_revision = "0024_ver_num_64"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "participations",
        sa.Column(
            "classification_id",
            sa.String(length=36),
            sa.ForeignKey("classifications.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_participations_classification_id"),
        "participations",
        ["classification_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_participations_classification_id"), table_name="participations")
    op.drop_column("participations", "classification_id")
