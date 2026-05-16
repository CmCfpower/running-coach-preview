"""Athlete profile service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from running_coach.storage import ProjectStorage


@dataclass(frozen=True)
class ProfileStatus:
    profile: dict[str, Any]
    missing_fields: tuple[str, ...]
    is_usable: bool


IMPORTANT_FIELDS = (
    "age",
    "sex",
    "height_cm",
    "weight_kg",
    "goals",
    "training_days_per_week",
    "available_training_days",
)


def load_profile(storage: ProjectStorage) -> ProfileStatus:
    profile = storage.read_yaml("data", "profile.yaml")
    missing = tuple(field for field in IMPORTANT_FIELDS if _is_empty(profile.get(field)))
    return ProfileStatus(
        profile=profile,
        missing_fields=missing,
        is_usable=len(missing) == 0,
    )


def format_profile_summary(status: ProfileStatus) -> str:
    profile = status.profile
    goals = [goal for goal in profile.get("goals", []) if goal]
    days = profile.get("available_training_days", [])

    lines = [
        "Профиль спортсмена",
        f"Имя: {profile.get('name') or 'не указано'}",
        f"Возраст: {_value(profile.get('age'))}",
        f"Пол: {profile.get('sex') or 'не указано'}",
        f"Рост/вес: {_value(profile.get('height_cm'))} см / {_value(profile.get('weight_kg'))} кг",
        f"Тренировок в неделю: {_value(profile.get('training_days_per_week'))}",
        f"Доступные дни: {', '.join(days) if days else 'не указано'}",
        f"Цели: {', '.join(goals) if goals else 'не указано'}",
    ]

    if status.missing_fields:
        lines.append("")
        lines.append("Нужно заполнить: " + ", ".join(status.missing_fields))

    return "\n".join(lines)


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if value == "":
        return True
    if isinstance(value, list):
        return len([item for item in value if item]) == 0
    return False


def _value(value: Any) -> str:
    return "не указано" if value is None or value == "" else str(value)
