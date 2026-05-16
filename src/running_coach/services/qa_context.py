"""Compact context builder for running-qa-agent."""

from __future__ import annotations

import json
from datetime import date, timedelta
from typing import Any

from running_coach.storage import ProjectStorage
from running_coach.services.profile import load_profile
from running_coach.services.training_plan import load_current_training_plan
from running_coach.services.workouts import load_workout_for_date


_RECENT_DAYS = 14
_MAX_PLAN_DAYS = 10


def build_qa_context(
    storage: ProjectStorage,
    question: str,
    *,
    today: date | None = None,
) -> dict[str, Any]:
    """Gather compact context for the QA agent."""
    today = today or date.today()

    profile_status = load_profile(storage)
    plan = _safe_load(lambda: load_current_training_plan(storage))
    recent_workouts = _load_recent_workouts(storage, today)
    weekly_summary = _load_weekly_summary(storage, today)
    feedback_recent = _load_recent_feedback(storage, today)

    return {
        "question": question,
        "today": today.isoformat(),
        "profile": _compact_profile(profile_status.profile),
        "current_plan": _compact_plan(plan, today),
        "recent_workouts": recent_workouts,
        "weekly_summary": weekly_summary,
        "recent_feedback": feedback_recent,
    }


def format_qa_prompt(context: dict[str, Any], prompt_template: str) -> str:
    """Append structured context block to the system prompt."""
    ctx_block = json.dumps(context, ensure_ascii=False, indent=2)
    return f"{prompt_template}\n\n## Context\n\n```json\n{ctx_block}\n```"


# --- private helpers ---

def _compact_profile(profile: dict[str, Any]) -> dict[str, Any]:
    keys = ("name", "age", "sex", "weight_kg", "height_cm", "goals",
            "training_days_per_week", "available_training_days",
            "max_hr", "resting_hr", "injuries", "notes")
    return {k: profile[k] for k in keys if k in profile and profile[k] not in (None, "", [])}


def _compact_plan(plan: dict[str, Any] | None, today: date) -> dict[str, Any] | None:
    if not plan:
        return None
    cutoff = today + timedelta(days=_MAX_PLAN_DAYS)
    days = [
        {k: d[k] for k in ("date", "type", "duration_min", "distance_km", "instructions")
         if k in d and d[k] is not None}
        for d in plan.get("days", [])
        if d.get("date") and today.isoformat() <= d["date"] <= cutoff.isoformat()
    ]
    return {
        "week_start": plan.get("week_start"),
        "week_end": plan.get("week_end"),
        "goal": plan.get("goal"),
        "days": days,
    }


def _load_recent_workouts(storage: ProjectStorage, today: date) -> list[dict[str, Any]]:
    result = []
    for offset in range(_RECENT_DAYS):
        d = today - timedelta(days=offset)
        workout = _safe_load(lambda d=d: load_workout_for_date(storage, d.isoformat()))
        if workout:
            result.append(_compact_workout(workout, d.isoformat()))
    return result


def _compact_workout(w: dict[str, Any], workout_date: str) -> dict[str, Any]:
    keys = ("distance_km", "duration_sec", "avg_pace_sec_per_km", "avg_hr",
            "max_hr", "workout_type", "notes")
    out: dict[str, Any] = {"date": workout_date}
    out.update({k: w[k] for k in keys if k in w and w[k] not in (None, [])})
    return out


def _load_weekly_summary(storage: ProjectStorage, today: date) -> list[dict[str, Any]]:
    history = _safe_load(lambda: storage.read_json("data", "derived", "history_summary.json"))
    if not history:
        return []
    weekly = history.get("weekly") or []
    cutoff = (today - timedelta(weeks=3)).isoformat()[:7]  # YYYY-MM
    result = []
    for week in weekly:
        week_start = str(week.get("week_start") or "")
        if week_start >= cutoff:
            result.append({
                "week_start": week_start,
                "distance_km": week.get("distance_km"),
                "workouts": week.get("count"),
                "avg_hr": week.get("avg_hr"),
            })
    return result[-4:]  # last 4 weeks max


def _load_recent_feedback(storage: ProjectStorage, today: date) -> list[dict[str, Any]]:
    try:
        records = storage.read_json("data", "feedback", "training_feedback.json")
    except (FileNotFoundError, Exception):
        return []
    if not isinstance(records, list):
        return []
    cutoff = (today - timedelta(days=14)).isoformat()
    recent = [
        {"date": r.get("date"), "type": r.get("type"), "signals": r.get("signals", [])}
        for r in records
        if isinstance(r, dict) and str(r.get("date") or "") >= cutoff
    ]
    return recent[-7:]


def _safe_load(fn):
    try:
        return fn()
    except Exception:
        return None
