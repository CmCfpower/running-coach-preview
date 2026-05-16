"""LLM-backed coach review for plan/fact mismatches."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from running_coach.llm import LlmError, OpenAICompatibleClient
from running_coach.services.profile import load_profile
from running_coach.storage import ProjectStorage


def build_coach_review_context(
    storage: ProjectStorage,
    *,
    target_date: str,
    plan: dict[str, Any],
    day_plan: dict[str, Any] | None,
    actual_workout: dict[str, Any] | None,
    feedback: dict[str, Any] | None,
) -> dict[str, Any]:
    profile_status = load_profile(storage)
    return {
        "target_date": target_date,
        "athlete_profile": _compact_profile(profile_status.profile),
        "current_day_plan": day_plan,
        "actual_workout": _compact_workout(actual_workout),
        "feedback": feedback,
        "next_days": _next_days(plan, target_date, limit=3),
        "plan_warnings": plan.get("warnings", []),
    }


def request_coach_plan_review(
    storage: ProjectStorage,
    client: OpenAICompatibleClient,
    *,
    context: dict[str, Any],
    prompt_path: Path,
) -> dict[str, Any]:
    prompt = prompt_path.read_text(encoding="utf-8")
    content = client.chat(
        [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": json.dumps(context, ensure_ascii=False, indent=2),
            },
        ],
        temperature=0.2,
    )
    review = _parse_json_object(content)
    review.setdefault("summary", "Тренер посмотрел расхождение плана и факта.")
    review.setdefault("risk_level", "medium")
    review.setdefault("reasoning", [])
    review.setdefault("plan_changes", [])
    review.setdefault("telegram_message", review["summary"])
    review.setdefault("needs_clarification", False)
    review.setdefault("clarification_question", None)
    review["created_at"] = datetime.now(timezone.utc).isoformat()
    review["target_date"] = context.get("target_date")
    return review


def save_coach_review(storage: ProjectStorage, target_date: str, review: dict[str, Any]) -> str:
    path = storage.resolve("data", "coach_reviews", f"{target_date}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return storage.relative(path)


def format_coach_review_message(review: dict[str, Any], saved_path: str | None = None) -> str:
    lines = ["Тренер посмотрел план vs факт."]
    message = review.get("telegram_message") or review.get("summary")
    if message:
        lines.append(str(message))

    changes = review.get("plan_changes") or []
    if changes:
        lines.append("")
        lines.append("Корректировка:")
        for change in changes[:3]:
            date_text = change.get("date", "дата")
            current_type = change.get("current_type", "?")
            recommended_type = change.get("recommended_type", "?")
            summary = change.get("change_summary") or change.get("instructions") or ""
            lines.append(f"- {date_text}: {current_type} -> {recommended_type}. {summary}".strip())

    if review.get("needs_clarification") and review.get("clarification_question"):
        lines.append("")
        lines.append(str(review["clarification_question"]))

    if saved_path:
        lines.append("")
        lines.append(f"Review сохранён: {saved_path}")

    return "\n".join(lines)


def _parse_json_object(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.removeprefix("json").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LlmError(f"Coach review did not return JSON: {content[:300]}")
    try:
        parsed = json.loads(cleaned[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LlmError(f"Coach review JSON parse failed: {content[:300]}") from exc
    if not isinstance(parsed, dict):
        raise LlmError("Coach review JSON root must be an object")
    return parsed


def _compact_profile(profile: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "age",
        "sex",
        "height_cm",
        "weight_kg",
        "resting_hr",
        "max_hr",
        "goals",
        "training_days_per_week",
        "available_training_days",
        "limitations",
    )
    return {key: profile.get(key) for key in keys}


def _compact_workout(workout: dict[str, Any] | None) -> dict[str, Any] | None:
    if workout is None:
        return None
    keys = (
        "id",
        "date",
        "sport",
        "distance_km",
        "duration_sec",
        "avg_pace_sec_per_km",
        "avg_hr",
        "max_hr",
        "elevation_gain_m",
        "rpe",
        "extraction_confidence",
    )
    return {key: workout.get(key) for key in keys}


def _next_days(plan: dict[str, Any], target_date: str, *, limit: int) -> list[dict[str, Any]]:
    days = [
        day
        for day in plan.get("days", [])
        if isinstance(day, dict) and str(day.get("date", "")) >= target_date
    ]
    return days[:limit]
