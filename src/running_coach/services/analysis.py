"""Formatting for coaching analysis shown in Telegram."""

from __future__ import annotations

from typing import Any

from running_coach.storage import ProjectStorage


def load_coaching_report(storage: ProjectStorage) -> dict[str, Any]:
    return storage.read_json("data", "derived", "coaching_report.json")


def format_analysis(report: dict[str, Any]) -> str:
    readiness = report.get("readiness", {})
    plan = report.get("plan", {})
    days = plan.get("days", [])
    risks = report.get("risks", [])
    recommendations = report.get("recommendations", [])
    key_findings = report.get("key_findings", [])

    lines = [
        "Анализ формы",
        f"Старт: {report.get('race_date', '-')}",
        f"До старта: {report.get('days_to_race', '-')} дней",
        "",
        f"Готовность: {readiness.get('status', '-')}",
        readiness.get("comment", ""),
    ]

    if key_findings:
        lines.extend(["", "Ключевое:"])
        lines.extend(f"- {item}" for item in key_findings[:4])

    if risks:
        lines.extend(["", "Риски:"])
        lines.extend(f"- {item}" for item in risks[:3])

    if recommendations:
        lines.extend(["", "Что делать сейчас:"])
        lines.extend(f"- {item}" for item in recommendations[:3])

    upcoming = days[:4]
    if upcoming:
        lines.extend(["", "Ближайшие дни:"])
        for day in upcoming:
            lines.append(f"- {day.get('date')}: {day.get('type')} - {day.get('title')}")

    return "\n".join(line for line in lines if line is not None)
