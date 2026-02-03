"""Penalty: drop participation_id, incident_id NOT NULL. Penalty belongs to Incident only.

Revision ID: 0039_penalty_drop_part_id
Revises: 0038_drop_part_counts
Create Date: 2026-01-30

"""
import uuid
from alembic import op
import sqlalchemy as sa

revision = "0039_penalty_drop_part_id"
down_revision = "0038_drop_part_counts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Backfill: for each penalty with incident_id NULL, create a placeholder incident and link it
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id, participation_id FROM penalties WHERE incident_id IS NULL")
    ).fetchall()
    for (penalty_id, participation_id) in rows:
        # Insert minimal incident for this participation
        incident_id = str(uuid.uuid4())
        conn.execute(
            sa.text(
                "INSERT INTO incidents (id, participation_id, incident_type, severity, code, score, created_at) "
                "VALUES (:id, :participation_id, 'Other', 1, 'legacy', 0, NOW() AT TIME ZONE 'UTC')"
            ),
            {"id": incident_id, "participation_id": participation_id},
        )
        conn.execute(
            sa.text("UPDATE penalties SET incident_id = :incident_id WHERE id = :penalty_id"),
            {"incident_id": incident_id, "penalty_id": penalty_id},
        )

    # 2) Make incident_id NOT NULL and add CASCADE
    op.alter_column(
        "penalties",
        "incident_id",
        existing_type=sa.String(36),
        nullable=False,
    )
    op.drop_constraint(
        "fk_penalties_incident_id_incidents",
        "penalties",
        type_="foreignkey",
    )
    op.create_foreign_key(
        "fk_penalties_incident_id_incidents",
        "penalties",
        "incidents",
        ["incident_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 3) Drop participation_id
    op.drop_index("ix_penalties_participation_id", table_name="penalties", if_exists=True)
    op.drop_constraint(
        "penalties_participation_id_fkey",
        "penalties",
        type_="foreignkey",
    )
    op.drop_column("penalties", "participation_id")


def downgrade() -> None:
    op.add_column(
        "penalties",
        sa.Column("participation_id", sa.String(36), nullable=True),
    )
    op.create_foreign_key(
        "penalties_participation_id_fkey",
        "penalties",
        "participations",
        ["participation_id"],
        ["id"],
    )
    op.create_index("ix_penalties_participation_id", "penalties", ["participation_id"])

    # Backfill participation_id from incident
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE penalties p SET participation_id = (SELECT participation_id FROM incidents i WHERE i.id = p.incident_id)"
        )
    )
    op.alter_column(
        "penalties",
        "participation_id",
        existing_type=sa.String(36),
        nullable=False,
    )

    op.drop_constraint("fk_penalties_incident_id_incidents", "penalties", type_="foreignkey")
    op.create_foreign_key(
        "fk_penalties_incident_id_incidents",
        "penalties",
        "incidents",
        ["incident_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.alter_column(
        "penalties",
        "incident_id",
        existing_type=sa.String(36),
        nullable=True,
    )
