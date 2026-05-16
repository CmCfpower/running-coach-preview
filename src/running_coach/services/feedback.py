"""Training feedback classification and storage."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from running_coach.storage import ProjectStorage


KEYWORDS: dict[str, tuple[str, ...]] = {
    "completed": ("сделал", "выполнил", "пробежал", "отбегал", "готово"),
    "hard": ("тяжело", "сложно", "еле", "устал", "забился", "разобрало"),
    "easy": ("легко", "комфортно", "нормально", "хорошо", "ок"),
    "missed": ("пропустил", "не сделал", "не побежал", "не успел"),
    "moved": ("перенес", "перенёс", "перенести", "перенесу", "сдвинул"),
    "high_hr": ("пульс высокий", "высокий пульс", "чсс высок", "пульс выше"),
    "pain": ("боль", "болит", "травма", "потянул", "колено", "ахилл"),
}

PLAN_REVIEW_SIGNALS = {"hard", "missed", "moved", "high_hr", "pain"}


def classify_training_feedback(text: str, current_date: date | None = None) -> dict[str, Any] | None:
    """Classify short Russian post-workout feedback without an LLM call."""

    normalized = _normalize(text)
    if not normalized:
        return None

    signals = [
        signal
        for signal, keywords in KEYWORDS.items()
        if any(_contains_keyword(normalized, keyword) for keyword in keywords)
    ]
    if not signals:
        return None

    target_date = _date_from_text(normalized) or (current_date or date.today()).isoformat()
    requires_plan_review = any(signal in PLAN_REVIEW_SIGNALS for signal in signals)

    confidence = 0.72 + min(len(signals), 3) * 0.07
    if "completed" in signals and ("hard" in signals or "easy" in signals):
        confidence += 0.07

    return {
        "type": "training_feedback",
        "date": target_date,
        "raw_text": text.strip(),
        "signals": signals,
        "confidence": round(min(confidence, 0.95), 2),
        "requires_plan_review": requires_plan_review,
        "notes": _notes_for_signals(signals),
    }


def append_training_feedback(
    storage: ProjectStorage,
    feedback: dict[str, Any],
    *,
    source: str,
) -> Path:
    """Append a feedback event to a project-local JSONL file."""

    path = storage.resolve("data", "feedback", "training_feedback.jsonl")
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source": source,
        **feedback,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def load_training_feedback(storage: ProjectStorage, limit: int = 20) -> list[dict[str, Any]]:
    """Read recent training feedback events from the project JSONL log."""

    path = storage.resolve("data", "feedback", "training_feedback.jsonl")
    if not path.exists():
        return []

    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events[-limit:]


def plan_feedback_notes(events: list[dict[str, Any]], target_date: date | None = None) -> list[str]:
    """Convert recent feedback into conservative plan notes."""

    if not events:
        return []

    notes: list[str] = []
    relevant = [
        event
        for event in events
        if event.get("requires_plan_review")
        and (target_date is None or event.get("date") <= target_date.isoformat())
    ]
    if not relevant:
        return []

    recent_signals: set[str] = set()
    for event in relevant[-3:]:
        recent_signals.update(event.get("signals") or [])

    if "pain" in recent_signals:
        notes.append("Есть свежий сигнал боли/травмы: интенсивную работу лучше не делать без проверки самочувствия.")
    if "high_hr" in recent_signals:
        notes.append("Есть свежий сигнал высокого пульса: держи тренировку легче и ориентируйся на HR/RPE.")
    if "hard" in recent_signals:
        notes.append("Последняя нагрузка отмечена как тяжёлая: сегодня не нужно добирать интенсивность.")
    if "missed" in recent_signals:
        notes.append("Был пропуск: не переносим весь объём автоматически, возвращаемся мягко.")
    if "moved" in recent_signals:
        notes.append("Есть запрос на перенос: план нужно сверить с календарём ближайших дней.")

    return notes


def format_feedback_response(feedback: dict[str, Any]) -> str:
    signals = set(feedback.get("signals", []))
    context = feedback.get("context") or {}
    if context.get("actual_workout_id"):
        lines = ["Фидбэк записал к фактической тренировке за этот день."]
    else:
        lines = ["Фидбэк записал, но фактической тренировки за этот день пока не вижу."]

    if context.get("planned_type") == "rest" and context.get("actual_workout_id"):
        lines.append("Важно: по плану был отдых, но факт тренировки уже записан. Учту это как расхождение плана и факта.")

    if "pain" in signals:
        lines.append("Если это боль или травма, лучше не усиливать нагрузку и при необходимости обратиться к врачу.")
    elif "high_hr" in signals:
        lines.append("Отмечаю высокий пульс: следующую качественную работу нужно проверить осторожно.")
    elif "hard" in signals:
        lines.append("Отмечаю высокую тяжесть: план стоит адаптировать по восстановлению.")
    elif "missed" in signals:
        lines.append("Отмечаю пропуск: не будем автоматически догонять нагрузку.")
    elif "moved" in signals:
        lines.append("Отмечаю перенос: это нужно учесть в ближайшем плане.")
    elif "easy" in signals:
        lines.append("Отмечаю, что нагрузка зашла комфортно.")

    if feedback.get("requires_plan_review"):
        lines.append("Позже running-plan-agent сможет пересобрать план с учётом этого сигнала.")

    return "\n".join(lines)


def _normalize(text: str) -> str:
    return " ".join(text.lower().replace("ё", "е").split())


def _date_from_text(text: str) -> str | None:
    # Keep this intentionally small; captions/photos already have richer date parsing.
    today = date.today()
    if "сегодня" in text:
        return today.isoformat()
    if "вчера" in text:
        return date.fromordinal(today.toordinal() - 1).isoformat()
    return None


def _contains_keyword(text: str, keyword: str) -> bool:
    if " " in keyword:
        return keyword in text
    return re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", text) is not None


def _notes_for_signals(signals: list[str]) -> list[str]:
    notes: list[str] = []
    if "completed" in signals:
        notes.append("workout completed")
    if "hard" in signals:
        notes.append("high perceived effort")
    if "easy" in signals:
        notes.append("low perceived effort")
    if "missed" in signals:
        notes.append("missed planned workout")
    if "moved" in signals:
        notes.append("schedule change requested")
    if "high_hr" in signals:
        notes.append("high heart-rate signal")
    if "pain" in signals:
        notes.append("pain or injury signal")
    return notes
