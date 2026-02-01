from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Event(Base):
    __tablename__ = "events"

    __table_args__ = (
        CheckConstraint("team_size_min <= team_size_max", name="ck_events_team_size_range"),
        CheckConstraint("team_size_min >= 1 AND team_size_min <= 8", name="ck_events_team_size_min_1_8"),
        CheckConstraint("team_size_max >= 1 AND team_size_max <= 8", name="ck_events_team_size_max_1_8"),
        CheckConstraint("duration_minutes >= 0 AND duration_minutes <= 1440", name="ck_events_duration_0_1440"),
        CheckConstraint("grid_size_expected >= 0 AND grid_size_expected <= 100", name="ck_events_grid_0_100"),
        CheckConstraint("class_count >= 1 AND class_count <= 6", name="ck_events_class_1_6"),
        CheckConstraint(
            "special_event IS NULL OR special_event IN ('race_of_day', 'race_of_week', 'race_of_month', 'race_of_year')",
            name="ck_events_special_event",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    source: Mapped[str] = mapped_column(String(40), nullable=False)
    game: Mapped[str | None] = mapped_column(String(60), nullable=True)

    country: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)

    start_time_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_time_utc: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Race of the day / week / month / year — special featured event (more points)
    special_event: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # в БД храним строку, в API валидируем Enum-ом
    session_type: Mapped[str] = mapped_column(String(20), nullable=False, default="race")  # race | training
    schedule_type: Mapped[str] = mapped_column(String(20), nullable=False, default="weekly")
    event_type: Mapped[str] = mapped_column(String(30), nullable=False, default="circuit")
    format_type: Mapped[str] = mapped_column(String(30), nullable=False, default="sprint")

    session_list: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    team_size_min: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    team_size_max: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    rolling_start: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pit_rules: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    grid_size_expected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    class_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    car_class_list: Mapped[list] = mapped_column(JSON, nullable=False, default=list)

    damage_model: Mapped[str] = mapped_column(String(20), nullable=False, default="off")
    penalties: Mapped[str] = mapped_column(String(20), nullable=False, default="off")
    fuel_usage: Mapped[str] = mapped_column(String(20), nullable=False, default="off")
    tire_wear: Mapped[str] = mapped_column(String(20), nullable=False, default="off")

    weather: Mapped[str] = mapped_column(String(20), nullable=False, default="fixed")

    night: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    time_acceleration: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    surface_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    track_type: Mapped[str | None] = mapped_column(String(20), nullable=True)

    stewarding: Mapped[str] = mapped_column(String(20), nullable=False, default="none")

    team_event: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    license_requirement: Mapped[str] = mapped_column(String(20), nullable=False, default="none")

    official_event: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    assists_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
