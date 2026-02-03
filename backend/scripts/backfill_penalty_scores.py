"""Backfill penalty.score where null: set from PENALTY_TYPE_SCORES by penalty_type.

Run from repo root:
  docker compose exec app python backend/scripts/backfill_penalty_scores.py [--dry-run]
"""
from __future__ import annotations

import sys

from app.db.session import SessionLocal
from app.models.penalty import Penalty
from app.penalties.scores import get_score_for_penalty_type


def main() -> None:
    dry_run = "--dry-run" in sys.argv
    session = SessionLocal()
    try:
        rows = session.query(Penalty).filter(Penalty.score.is_(None)).all()
        if not rows:
            print("No Penalty rows with null score.")
            return
        print(f"Found {len(rows)} penalty row(s) with null score.")
        for p in rows:
            score = get_score_for_penalty_type(p.penalty_type)
            print(f"  id={p.id[:8]}… incident_id={p.incident_id[:8] if p.incident_id else 'N/A'}… type={p.penalty_type} -> score={score}")
            if not dry_run:
                p.score = score
        if not dry_run and rows:
            session.commit()
            print(f"Updated {len(rows)} row(s).")
        elif dry_run:
            print("Dry run: no changes written.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
