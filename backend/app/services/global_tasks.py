"""
Глобальные задачи (не привязаны к event): регистр task_code → кастомная проверка готовности.

Использование:
  - После сохранения профиля / драйвера вызвать check_and_complete_global_tasks(session, driver_id).
  - Каждая задача описывается кодом и функцией (session, driver_id) -> bool (готов ли к завершению).
  - При True вызывается task_engine.complete_task; если задача уже completed, ничего не делаем.
"""
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.models.task_definition import TaskDefinition
from app.models.user_profile import UserProfile
from app.services.task_engine import can_complete_task, complete_task
from app.core.constants import (
    GT_GLOBAL_PROFILE,
    GT_GLOBAL_SIM_GAMES,
    PROFILE_REQUIRED_FIELDS,
)


def _is_profile_ready(session: Session, driver_id: str) -> bool:
    """Профиль считается готовым, если все обязательные поля заполнены."""
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    if not driver or not driver.user_id:
        return False
    profile = session.query(UserProfile).filter(UserProfile.user_id == driver.user_id).first()
    if not profile:
        return False
    for field in PROFILE_REQUIRED_FIELDS:
        value = getattr(profile, field, None)
        if field == "sim_platforms":
            if not value:
                return False
        else:
            if value in (None, ""):
                return False
    return True


def _has_sim_games(session: Session, driver_id: str) -> bool:
    """У драйвера выбран хотя бы один сим."""
    driver = session.query(Driver).filter(Driver.id == driver_id).first()
    if not driver:
        return False
    return bool(getattr(driver, "sim_games", None) and len(driver.sim_games) > 0)


# Регистр: task_code -> функция проверки (session, driver_id) -> bool
GLOBAL_TASK_CHECKS: dict[str, callable] = {
    GT_GLOBAL_PROFILE: _is_profile_ready,
    GT_GLOBAL_SIM_GAMES: _has_sim_games,
}


def check_and_complete_global_tasks(session: Session, driver_id: str) -> list[str]:
    """
    Проверить все зарегистрированные глобальные задачи; для тех, где проверка вернула True,
    вызвать complete_task (если ещё не completed). Возвращает список task_code, которые были завершены в этом вызове.
    """
    completed_now: list[str] = []
    for task_code, check_fn in GLOBAL_TASK_CHECKS.items():
        if not check_fn(session, driver_id):
            continue
        task = session.query(TaskDefinition).filter(TaskDefinition.code == task_code).first()
        if not task or not getattr(task, "active", True):
            continue
        allowed, _ = can_complete_task(session, driver_id, task.id, participation_id=None)
        if not allowed:
            continue
        completion = complete_task(session, driver_id=driver_id, task_code=task_code, participation_id=None)
        if completion:
            completed_now.append(task_code)
    if completed_now:
        session.commit()
    return completed_now
