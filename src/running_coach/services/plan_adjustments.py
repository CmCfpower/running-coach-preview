"""Draft plan adjustments built from coach reviews."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from running_coach.storage import ProjectStorage


def build_plan_adjustment_draft(
    *,
    target_date: str,
    review: dict[str, Any],
    plan: dict[str, Any],
    day_plan: dict[str, Any] | None,
    actual_workout: dict[str, Any] | None,
    feedback: dict[str, Any] | None,
    review_path: str,
) -> dict[str, Any] | None:
    """Create a safe, manual-review draft from coach review plan changes."""

    changes = _normalize_changes(review.get("plan_changes"), target_date=target_date)
    if not changes:
        return None

    return {
        "status": "draft",
        "mode": "manual_review",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "target_date": target_date,
        "source": {
            "type": "coach_review",
            "review_path": review_path,
            "risk_level": review.get("risk_level", "medium"),
            "needs_clarification": bool(review.get("needs_clarification", False)),
        },
        "context": {
            "planned_type": day_plan.get("type") if day_plan else None,
            "actual_workout_id": actual_workout.get("id") if actual_workout else None,
            "actual_distance_km": actual_workout.get("distance_km") if actual_workout else None,
            "feedback_signals": feedback.get("signals", []) if feedback else [],
            "plan_week_start": plan.get("week_start"),
            "plan_week_end": plan.get("week_end"),
        },
        "summary": review.get("summary") or review.get("telegram_message") or "",
        "reasoning": _string_list(review.get("reasoning")),
        "changes": changes,
        "safety": {
            "auto_apply_allowed": False,
            "reason": "Draft only. The current training plan is not changed automatically.",
            "max_days_changed": len(changes),
        },
    }


def save_plan_adjustment_draft(
    storage: ProjectStorage,
    target_date: str,
    draft: dict[str, Any],
) -> str:
    path = storage.resolve("data", "plan_adjustments", f"{target_date}.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return storage.relative(path)


def load_latest_adjustment_draft(storage: ProjectStorage) -> tuple[dict[str, Any], str] | None:
    """Return (draft, relative_path) for the most recent draft file, or None."""
    adj_dir = storage.resolve("data", "plan_adjustments")
    if not adj_dir.exists():
        return None
    files = sorted(adj_dir.glob("*.json"), reverse=True)
    for path in files:
        try:
            draft = json.loads(path.read_text(encoding="utf-8-sig"))
            if isinstance(draft, dict) and draft.get("status") not in {"invalidated", "rejected", "superseded"}:
                return draft, storage.relative(path)
        except (json.JSONDecodeError, OSError):
            continue
    return None


def format_adjustment_for_display(draft: dict[str, Any]) -> str:
    status = draft.get("status", "draft")
    created = draft.get("created_at", "")[:10]
    target_date = draft.get("target_date") or "?"
    summary = draft.get("summary") or ""
    reasoning = draft.get("reasoning") or []
    changes = draft.get("changes") or []
    source = draft.get("source") or {}
    context = draft.get("context") or {}
    safety = draft.get("safety") or {}

    lines = [
        f"Черновик коррекции [{status}] от {created}",
        f"Дата события: {target_date}",
    ]
    if source.get("risk_level"):
        lines.append(f"Риск: {source.get('risk_level')}")
    if context.get("actual_workout_id"):
        lines.append(f"Тренировка: {context.get('actual_workout_id')}")
    if safety.get("max_days_changed"):
        lines.append(f"Затрагивает дней: {safety.get('max_days_changed')}")
    if summary:
        lines += ["", summary]
    if reasoning:
        lines += ["", "Обоснование:"]
        lines.extend(f"- {r}" for r in reasoning[:3])
    if changes:
        lines += ["", "Предложенные изменения:"]
        for ch in changes:
            day_line = f"- {ch.get('date')}: {ch.get('current_type')} -> {ch.get('recommended_type')}"
            if ch.get("change_summary"):
                day_line += f"  ({ch['change_summary']})"
            lines.append(day_line)
            if ch.get("instructions"):
                lines.append(f"  {ch['instructions']}")

    lines += [
        "",
        "Основной план НЕ изменяется автоматически.",
    ]
    if status == "draft":
        lines.append("Применить: /apply_adjustment")
        lines.append("Отклонить: /reject_adjustment")
    elif status == "applied":
        lines.append("Этот черновик уже применён к плану.")
    elif status in {"rejected", "invalidated", "superseded"}:
        lines.append("Этот черновик не активен и не будет применён.")

    return "\n".join(lines)


def apply_adjustment_to_plan(
    storage: ProjectStorage,
    draft: dict[str, Any],
) -> tuple[int, list[str]]:
    """Apply proposed changes to the current training plan.

    Only changes dated between today and today+3 are written.
    Returns (applied_count, skipped_dates).
    """
    from running_coach.services.training_plan import load_current_training_plan

    today = date.today()
    horizon = today + timedelta(days=3)
    changes = draft.get("changes") or []

    if draft.get("status") != "draft":
        return 0, [f"status={draft.get('status')}"]

    plan = load_current_training_plan(storage)
    days_index: dict[str, dict[str, Any]] = {d["date"]: d for d in plan.get("days", []) if "date" in d}

    applied: list[str] = []
    skipped: list[str] = []

    for ch in changes:
        ch_date_str = ch.get("date") or ""
        try:
            ch_date = date.fromisoformat(ch_date_str)
        except ValueError:
            skipped.append(ch_date_str or "?")
            continue

        if ch_date < today or ch_date > horizon:
            skipped.append(ch_date_str)
            continue

        if ch_date_str not in days_index:
            skipped.append(ch_date_str)
            continue

        day = days_index[ch_date_str]
        if ch.get("recommended_type"):
            day["type"] = ch["recommended_type"]
        if ch.get("instructions"):
            day["instructions"] = ch["instructions"]
        applied.append(ch_date_str)

    if applied:
        plan_path = storage.resolve("data", "derived", "current_training_plan.json")
        plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return len(applied), skipped


def mark_adjustment_rejected(storage: ProjectStorage, draft_date: str, *, reason: str = "Rejected by user") -> bool:
    path = storage.resolve("data", "plan_adjustments", f"{draft_date}.json")
    if not path.exists():
        return False
    draft = json.loads(path.read_text(encoding="utf-8-sig"))
    if draft.get("status") == "applied":
        return False
    draft["status"] = "rejected"
    draft["rejected_at"] = datetime.now(timezone.utc).isoformat()
    draft["rejection_reason"] = reason
    path.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def mark_adjustment_applied(storage: ProjectStorage, draft_date: str) -> None:
    path = storage.resolve("data", "plan_adjustments", f"{draft_date}.json")
    if not path.exists():
        return
    draft = json.loads(path.read_text(encoding="utf-8-sig"))
    draft["status"] = "applied"
    draft["applied_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def format_plan_adjustment_notice(adjustment_path: str | None) -> str | None:
    if not adjustment_path:
        return None
    return (
        "Черновик коррекции сохранён. Основной план пока не меняю автоматически.\n"
        f"Файл: {adjustment_path}"
    )


def _normalize_changes(raw_changes: Any, *, target_date: str) -> list[dict[str, Any]]:
    if not isinstance(raw_changes, list):
        return []

    changes: list[dict[str, Any]] = []
    for raw_change in raw_changes:
        if not isinstance(raw_change, dict):
            continue

        change_date = str(raw_change.get("date") or "").strip()
        if not change_date or change_date < target_date:
            continue

        changes.append(
            {
                "date": change_date,
                "current_type": _nullable_text(raw_change.get("current_type")),
                "recommended_type": _nullable_text(raw_change.get("recommended_type")),
                "change_summary": _nullable_text(raw_change.get("change_summary")),
                "instructions": _nullable_text(raw_change.get("instructions")),
                "status": "proposed",
            }
        )

        if len(changes) >= 3:
            break

    return changes


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None]


def _nullable_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
