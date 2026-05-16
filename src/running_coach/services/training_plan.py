"""Training plan service."""

from __future__ import annotations

from datetime import date
from typing import Any

from running_coach.storage import ProjectStorage
from running_coach.services.workouts import format_workout_fact


def load_current_training_plan(storage: ProjectStorage) -> dict[str, Any]:
    return storage.read_json("data", "derived", "current_training_plan.json")


def find_day_plan(plan: dict[str, Any], target_date: date) -> dict[str, Any] | None:
    target = target_date.isoformat()
    for day in plan.get("days", []):
        if day.get("date") == target:
            return day
    return None


def format_day_plan(
    day: dict[str, Any] | None,
    target_date: date,
    feedback_notes: list[str] | None = None,
    actual_workout: dict[str, Any] | None = None,
) -> str:
    if day is None:
        return f"На {target_date.isoformat()} план не найден."

    workout_type = day.get("type", "unknown")
    duration = day.get("duration_min")
    distance = day.get("distance_km")
    instructions = day.get("instructions") or "Инструкции не указаны."
    warnings = day.get("warnings", [])

    lines = [
        f"План на {target_date.isoformat()}",
        f"Тип: {workout_type}",
    ]

    if duration is not None:
        lines.append(f"Длительность: {duration} мин")
    if distance is not None:
        lines.append(f"Дистанция: {distance} км")

    hr_range = _range(day.get("target_hr_min"), day.get("target_hr_max"))
    pace_range = _pace_range(
        day.get("target_pace_min_sec_per_km"),
        day.get("target_pace_max_sec_per_km"),
    )

    if hr_range:
        lines.append(f"Пульс: {hr_range}")
    if pace_range:
        lines.append(f"Темп: {pace_range}")

    lines.append("")
    lines.append(instructions)

    if actual_workout:
        lines.append("")
        lines.append(format_workout_fact(actual_workout))
        if workout_type == "rest":
            lines.append("Расхождение: в плане был отдых, но за день уже есть фактическая тренировка.")
        elif workout_type not in {"race", "unknown"}:
            lines.append("Факт тренировки найден, план на день нужно сверить с реальной нагрузкой.")

    if warnings:
        lines.append("")
        lines.append("Предупреждения:")
        lines.extend(f"- {warning}" for warning in warnings)

    if feedback_notes:
        lines.append("")
        lines.append("С учётом последнего фидбэка:")
        lines.extend(f"- {note}" for note in feedback_notes)

    return "\n".join(lines)


def format_week_plan(plan: dict[str, Any], feedback_notes: list[str] | None = None) -> str:
    lines = [
        f"План недели {plan.get('week_start')} - {plan.get('week_end')}",
        plan.get("summary", ""),
        "",
    ]

    for day in plan.get("days", []):
        duration = day.get("duration_min")
        duration_text = f", {duration} мин" if duration is not None else ""
        lines.append(f"{day.get('date')}: {day.get('type')}{duration_text}")

    warnings = plan.get("warnings", [])
    if warnings:
        lines.append("")
        lines.append("Предупреждения:")
        lines.extend(f"- {warning}" for warning in warnings)

    if feedback_notes:
        lines.append("")
        lines.append("С учётом последнего фидбэка:")
        lines.extend(f"- {note}" for note in feedback_notes)

    return "\n".join(line for line in lines if line is not None)


def _range(start: Any, end: Any) -> str | None:
    if start is None or end is None:
        return None
    return f"{start}-{end}"


def _pace_range(start: Any, end: Any) -> str | None:
    if start is None or end is None:
        return None
    return f"{_format_pace(start)}-{_format_pace(end)} мин/км"


def _format_pace(seconds: int) -> str:
    minutes, rest = divmod(int(seconds), 60)
    return f"{minutes}:{rest:02d}"
