"""Report how and for what penalties are counted for a user (by email or user_id).

CRS uses: for each participation, if there are Penalty rows → sum(penalty.score);
otherwise → participation.penalties_count * 6.0 (legacy).

Run from repo root:
  docker compose exec app python backend/scripts/report_penalties_by_user.py <email_or_user_id>

Example:
  docker compose exec app python backend/scripts/report_penalties_by_user.py vasilevigor3@gmail.com
"""
from __future__ import annotations

import sys
from datetime import datetime

from app.db.session import SessionLocal
from app.models.driver import Driver
from app.models.participation import Participation
from app.models.user import User
from app.penalties.scores import PENALTY_TYPE_SCORES, DEFAULT_PENALTY_SCORE, get_score_for_penalty_type
from app.repositories.driver import DriverRepository
from app.repositories.event import EventRepository
from app.repositories.penalty import PenaltyRepository
from app.repositories.user import UserRepository


def _format_dt(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%Y-%m-%d %H:%M") if hasattr(dt, "strftime") else str(dt)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: report_penalties_by_user.py <email_or_user_id>", file=sys.stderr)
        sys.exit(1)
    arg = sys.argv[1].strip()
    session = SessionLocal()
    try:
        user_repo = UserRepository(session)
        driver_repo = DriverRepository(session)
        penalty_repo = PenaltyRepository(session)
        event_repo = EventRepository(session)

        user = user_repo.get_by_email(arg)
        if not user:
            user = session.query(User).filter(User.id == arg).first()
        if not user:
            print(f"No user found for: {arg}")
            sys.exit(1)

        driver = driver_repo.get_by_user_id(user.id)
        if not driver:
            print(f"No driver for user id={user.id} email={user.email}")
            sys.exit(1)

        print("=" * 60)
        print("PENALTY SCORES (CRS deduction per penalty type)")
        print("=" * 60)
        for ptype, score in PENALTY_TYPE_SCORES.items():
            print(f"  {ptype}: {score}")
        print(f"  (default if missing: {DEFAULT_PENALTY_SCORE})")
        print()

        print("=" * 60)
        print(f"User: {user.email} (user_id={user.id})")
        print(f"Driver: id={driver.id}")
        print("=" * 60)

        participations = (
            session.query(Participation)
            .filter(Participation.driver_id == driver.id)
            .order_by(Participation.created_at.desc())
            .limit(30)
            .all()
        )
        if not participations:
            print("No participations.")
            return

        total_deduction_used = 0.0
        for p in participations:
            event = event_repo.get_by_id(p.event_id)
            event_title = event.title if event else p.event_id[:8] + "…"
            penalty_rows = penalty_repo.list_by_participation_id(p.id)
            penalty_score_sum = penalty_repo.sum_score_by_participation_id(p.id)
            penalty_count = penalty_repo.count_filtered(participation_id=p.id)

            if penalty_count > 0:
                deduction_used = penalty_score_sum
                source = "sum(penalty.score) from Penalty rows"
            else:
                deduction_used = p.penalties_count * 6.0
                source = f"legacy: penalties_count * 6.0 = {p.penalties_count} * 6"

            total_deduction_used += deduction_used

            print("-" * 60)
            print(f"Participation: {p.id[:8]}…  event: {event_title}")
            print(f"  status={p.status}  incidents_count={p.incidents_count}  penalties_count={p.penalties_count}")
            print(f"  Penalty rows in DB: {penalty_count}")
            print(f"  CRS deduction for this participation: {deduction_used:.1f}  ({source})")
            if penalty_rows:
                for i, pen in enumerate(penalty_rows, 1):
                    stored = pen.score if pen.score is not None else "null"
                    expected = get_score_for_penalty_type(pen.penalty_type)
                    time_s = f" +{pen.time_seconds}s" if pen.penalty_type == "time_penalty" and pen.time_seconds else ""
                    lap_s = f" lap={pen.lap}" if pen.lap is not None else ""
                    print(f"    {i}. id={pen.id[:8]}…  type={pen.penalty_type}{time_s}{lap_s}")
                    print(f"       score in DB: {stored}  (expected from map: {expected})  created={_format_dt(pen.created_at)}")
            elif p.penalties_count > 0:
                print(f"    (no Penalty rows; CRS uses penalties_count * 6 = {p.penalties_count * 6.0:.1f})")
            print()

        print("=" * 60)
        print(f"Total penalty deduction (last {len(participations)} participations): {total_deduction_used:.1f}")
        print("=" * 60)
    finally:
        session.close()


if __name__ == "__main__":
    main()
