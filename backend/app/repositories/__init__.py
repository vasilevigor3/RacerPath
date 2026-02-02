# Repositories: DB access layer (session + models).

from app.repositories.anti_gaming import AntiGamingReportRepository
from app.repositories.audit_log import AuditLogRepository
from app.repositories.classification import ClassificationRepository
from app.repositories.crs_history import CRSHistoryRepository
from app.repositories.driver import DriverRepository
from app.repositories.driver_license import DriverLicenseRepository
from app.repositories.event import EventRepository
from app.repositories.incident import IncidentRepository
from app.repositories.license_level import LicenseLevelRepository
from app.repositories.participation import ParticipationRepository
from app.repositories.raw_event import RawEventRepository
from app.repositories.real_world import RealWorldFormatRepository, RealWorldReadinessRepository
from app.repositories.recommendation import RecommendationRepository
from app.repositories.task_completion import TaskCompletionRepository
from app.repositories.task_definition import TaskDefinitionRepository
from app.repositories.tier_progression_rule import TierProgressionRuleRepository
from app.repositories.user import UserRepository
from app.repositories.user_profile import UserProfileRepository

__all__ = [
    "AntiGamingReportRepository",
    "AuditLogRepository",
    "ClassificationRepository",
    "CRSHistoryRepository",
    "DriverRepository",
    "DriverLicenseRepository",
    "EventRepository",
    "IncidentRepository",
    "LicenseLevelRepository",
    "ParticipationRepository",
    "RawEventRepository",
    "RealWorldFormatRepository",
    "RealWorldReadinessRepository",
    "RecommendationRepository",
    "TaskCompletionRepository",
    "TaskDefinitionRepository",
    "TierProgressionRuleRepository",
    "UserRepository",
    "UserProfileRepository",
]
