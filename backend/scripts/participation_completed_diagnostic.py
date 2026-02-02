"""Diagnose why PATCH participation -> completed might not trigger task/license.
Usage:
  docker compose exec app python backend/scripts/participation_completed_diagnostic.py <participation_id>
  docker compose exec app python backend/scripts/participation_completed_diagnostic.py --run-dispatch <participation_id>
"""
import sys
from datetime import datetime, timedelta, timezone

from app.db.session import SessionLocal
from app.models.participation import Participation, ParticipationState
from app.events.participation_events import dispatch_participation_completed


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python backend/scripts/participation_completed_diagnostic.py [--run-dispatch] <participation_id>", file=sys.stderr)
        sys.exit(1)
    run_dispatch = sys.argv[1] == "--run-dispatch"
    pid = sys.argv[2].strip() if run_dispatch else sys.argv[1].strip()
    session = SessionLocal()
    try:
        part = session.query(Participation).filter(Participation.id == pid).first()
        if not part:
            print(f"Participation not found: {pid}")
            sys.exit(1)
        state = part.participation_state
        state_str = state.value if hasattr(state, "value") else str(state)
        print(f"participation_id: {part.id}")
        print(f"driver_id: {part.driver_id}")
        print(f"participation_state: {state_str}")
        print(f"started_at: {part.started_at}")
        print(f"finished_at: {part.finished_at}")
        print(f"status: {getattr(part.status, 'value', part.status)}")
        if state_str != "completed":
            print("\n-> dispatch_participation_completed is only called when participation_state=completed.")
            print(f"   Current state is '{state_str}', so dispatch was not run.")
        elif part.started_at is None:
            print("\n-> PATCH with participation_state=completed requires started_at. If you sent only completed+finished_at,")
            print("   backend returns 400 and never commits or calls dispatch.")
        elif part.finished_at is None:
            print("\n-> completed requires finished_at. PATCH would return 400; dispatch not run.")
        else:
            print("\n-> State is completed with started_at and finished_at. Dispatch should have been called after PATCH.")
        if run_dispatch and state_str == "completed" and part.started_at and part.finished_at:
            print("\nRunning dispatch_participation_completed...")
            dispatch_participation_completed(session, part.driver_id, part.id)
            session.commit()
            print("Done. Tasks and license recalculated.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
