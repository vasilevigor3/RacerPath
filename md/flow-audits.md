# Flow Audits

Цель: точечные аудиты ключевых потоков с фокусом на корректность, безопасность и качество данных.

## Auth / Users
- Проверить: защита `/auth/bootstrap`, регистрация, логин, ротация API key.
- Проверить: требования к паролю и хэширование (PBKDF2), тайминг атаки.
- Проверить: роли и доступы на всех admin/coach эндпоинтах.
- Проверить: аудит логов и чувствительные поля (не логируются пароли/ключи).
Findings:
- Нет rate limiting для register/login: `backend/app/api/routes/auth.py`.
- Слабая валидация email (только "@"): `backend/app/api/routes/auth.py`.
- Пароли валидируются только по длине: `backend/app/schemas/auth.py`.
- AUTH_ENABLED по умолчанию `false`, защита может быть выключена: `backend/app/core/settings.py`.
- Bootstrap key по умолчанию "change-me": `backend/app/core/settings.py`.
- Нет logout/ревокации ключей, login всегда ротирует API key.

## Profile / Onboarding
- Проверить: согласованность данных профиля и driver, источники истины.
- Проверить: обязательность onboarding полей и валидации.
- Проверить: доступы на `/profile/me` и корректность обновлений.
Findings:
- Update профиля использует `setattr` по `model_dump()` без whitelist: `backend/app/api/routes/profile.py`.
- `sim_platforms` и `sim_games` принимают любые строки без валидации: `backend/app/schemas/profile.py`, `backend/app/schemas/driver.py`.

## Drivers
- Проверить: создание driver (включая `/drivers/me`) и повторные записи.
- Проверить: фильтрацию и пагинацию (если есть) на списках.
- Проверить: доступ к чужим driver данным.
Findings:
- Нет auth на `POST /drivers`, `GET /drivers`, `GET /drivers/{id}`: `backend/app/api/routes/drivers.py`.
- Нет проверки `user_id` при создании driver (валидность/существование).
- Возможны дубликаты drivers (нет уникальности), гонка при `create_my_driver`.

## Events / Classify
- Проверить: соответствие схемы события и классификации (inputs/outputs).
- Проверить: повторная классификация и консистентность записей.
- Проверить: кэш Redis и корректный fallback без Redis.
Findings:
- Публичный `POST /classify` и `POST /events/{id}/classify`: `backend/app/api/routes/classify.py`, `events.py`.
- `GET /events/{id}/classification(s)` без auth.
- Нет уникального ограничения на `Classification.event_id`, возможны дубликаты.

## Participations / Incidents
- Проверить: связь participation -> incident, целостность FK.
- Проверить: доступ к participation чужого driver.
- Проверить: корректность durations, дисциплин, дисциплина vs event.
Findings:
- Нет auth на создание/листинг/получение participations и incidents.
- Нет проверки владения participation при создании инцидента.
- `incidents_count` обновляется вручную, возможна рассинхронизация.
- Нет уникальности `(driver_id, event_id)` для participations.
- `incident_type` без enum-валидации: `backend/app/schemas/incident.py`.

## CRS
- Проверить: корректность формул, порядок вычислений, границы.
- Проверить: дублирующиеся расчеты и latest/history.
- Проверить: влияние внешних факторов (anti-gaming, tasks).
Findings:
- Все CRS эндпоинты публичные: `backend/app/api/routes/crs.py`.
- `multiplier` не ограничен, может быть отрицательным/слишком большим: `backend/app/services/crs.py`.
- Неявные дефолты для неизвестных tiers.

## Recommendations
- Проверить: фильтры по дисциплине/игре, tier range, readiness.
- Проверить: отсутствующие данные (нет CRS/participations).
- Проверить: стабильность и предсказуемость результатов.
Findings:
- Все recommendation эндпоинты публичные: `backend/app/api/routes/recommendations.py`.
- `_tier_in_range()` может бросить `ValueError` при неизвестном tier.
- Проверка лицензий использует `task.id` вместо `task.code`: `backend/app/services/recommendations.py`.

## Licenses / Tasks
- Проверить: правила повышения, авто-выдачи, ограничения.
- Проверить: автопроверку задач на participation creation.
- Проверить: анти-фарминг и кулдауны.
Findings:
- `POST /tasks/completions` и `POST /tasks/evaluate` без auth.
- Нет проверки, что participation принадлежит driver в `tasks/evaluate`.
- `requirements` в schema без структуры/валидации: `backend/app/schemas/task.py`.
- `GET /licenses` публичный, можно читать лицензии любых drivers.

## Anti-gaming
- Проверить: источники сигналов и корректность scoring.
- Проверить: влияние на CRS и рекомендации.
- Проверить: хранение отчетов и latest.
Findings:
- Все anti-gaming эндпоинты публичные: `backend/app/api/routes/anti_gaming.py`.
- `/reports` и `/reports/latest` без проверки существования driver.
- Нет пагинации для отчетов.

## Real-world readiness
- Проверить: соответствие форматам и дисциплинам.
- Проверить: интерпретацию readiness и пороги.
- Проверить: latest/history.
Findings:
- `/assess` и `/assessments` публичные, нет ownership check.
- Нет проверки существования driver для листинга.
- Нет уникальности `code` у форматов (возможны гонки): `backend/app/api/routes/real_world.py`.

## Ingestion / Connectors
- Проверить: контракт ingestion (raw_events) и нормализацию.
- Проверить: идемпотентность и дубликаты.
- Проверить: доступы и ограничение внешних синков.
Findings:
- Все ingestion/connector эндпоинты публичные.
- Нет проверки источника (source) и размера payload.
- Несколько commit в `ingest_payload`, возможна частичная запись.
- Нет защиты от дублей `source_event_id`.

## Admin / Operations
- Проверить: доступы, фильтры, поиск, доступ к чужим данным.
- Проверить: корректность обновлений профиля и связей user/driver.
Findings:
- Роль admin проверяется корректно: `backend/app/api/routes/admin.py`.
- Нет пагинации в `/admin/users` и поиске.
- Нет явной проверки существования user перед update profile.

## Metrics / Health
- Проверить: что не раскрывается чувствительная информация.
- Проверить: корректность счетчиков, нагрузка.
Findings:
- `/metrics` публичный, без rate limiting, может раскрывать объемы: `backend/app/api/routes/metrics.py`.
