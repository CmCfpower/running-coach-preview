"""Coaching analysis and near-race planning."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def build_half_marathon_report(history: dict[str, Any], *, today: date, race_date: date) -> dict[str, Any]:
    days_to_race = (race_date - today).days
    recent4 = history["recent_4_weeks"]
    recent6 = history["recent_6_weeks"]
    weekly = history["weekly"]
    last_weeks = weekly[-6:]
    longest = history["longest_workouts"][:5]

    return {
        "generated_at": today.isoformat(),
        "race_date": race_date.isoformat(),
        "days_to_race": days_to_race,
        "readiness": _readiness(history),
        "key_findings": [
            f"В анализе {history['analysis_records']} качественных записей из {history['total_records']}.",
            f"За последние 4 недели: {recent4['distance_km']} км и {recent4['workout_count']} тренировок.",
            f"За последние 6 недель: {recent6['distance_km']} км и {recent6['workout_count']} тренировок.",
            f"Самые длинные тренировки в базе: {', '.join(_format_longest(longest))}.",
            "Цель 1:59:59 требует среднего темпа около 5:41/км.",
        ],
        "risks": _risks(history, days_to_race),
        "recommendations": [
            "До старта уже не наращивать объём: главная задача - свежесть, сон и отсутствие травм.",
            "Оставить одну короткую работу около целевого темпа, без героизма и без добивания интервалов.",
            "Лёгкие пробежки держать разговорными; если пульс выше обычного, сокращать тренировку.",
            "На старте первые 3-5 км бежать сдержанно, затем стабилизироваться около целевого усилия.",
        ],
        "recent_weeks": last_weeks,
        "plan": _build_plan(today=today, race_date=race_date),
    }


def to_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Half Marathon Coaching Report",
        "",
        f"Generated at: {report['generated_at']}",
        f"Race date: {report['race_date']}",
        f"Days to race: {report['days_to_race']}",
        "",
        "## Readiness",
        "",
        f"Status: {report['readiness']['status']}",
        f"Comment: {report['readiness']['comment']}",
        "",
        "## Key Findings",
        "",
    ]
    lines.extend(f"- {item}" for item in report["key_findings"])
    lines.extend(["", "## Risks", ""])
    lines.extend(f"- {item}" for item in report["risks"])
    lines.extend(["", "## Recommendations", ""])
    lines.extend(f"- {item}" for item in report["recommendations"])
    lines.extend(["", "## Plan", ""])
    for day in report["plan"]["days"]:
        lines.append(
            f"- {day['date']} ({day['type']}): {day['title']}. {day['instructions']}"
        )
    lines.append("")
    return "\n".join(lines)


def _readiness(history: dict[str, Any]) -> dict[str, str]:
    recent4 = history["recent_4_weeks"]
    longest_distances = [item["distance_km"] for item in history["longest_workouts"][:5]]
    has_long_runs = any(distance >= 20 for distance in longest_distances if distance is not None)
    if recent4["distance_km"] >= 120 and has_long_runs:
        return {
            "status": "готов к аккуратному старту на результат",
            "comment": "База достаточная: есть регулярный объём и несколько длительных 20+ км.",
        }
    return {
        "status": "готов к финишу, результат зависит от свежести",
        "comment": "База есть, но перед стартом лучше выбирать консервативную тактику.",
    }


def _risks(history: dict[str, Any], days_to_race: int) -> list[str]:
    risks = []
    if days_to_race <= 14:
        risks.append("До старта меньше двух недель: большой объём или тяжёлая работа сейчас рискованнее, чем полезнее.")
    if history["partial_records"] or history["suspicious_records"]:
        risks.append("В истории есть записи на ручную проверку, поэтому точность отдельных недель не идеальна.")
    recent4 = history["recent_4_weeks"]
    if recent4["avg_pace_sec_per_km"] and recent4["avg_pace_sec_per_km"] > 450:
        risks.append("Средний темп последних недель спокойный: целевой темп полумарафона лучше проверять по пульсу и самочувствию.")
    return risks or ["Критичных рисков по истории не видно."]


def _build_plan(*, today: date, race_date: date) -> dict[str, Any]:
    days = []
    cursor = today
    while cursor <= race_date:
        days.append(_plan_day(cursor, race_date))
        cursor += timedelta(days=1)
    return {
        "start": today.isoformat(),
        "end": race_date.isoformat(),
        "days": days,
    }


def _plan_day(day: date, race_date: date) -> dict[str, Any]:
    days_to_race = (race_date - day).days
    weekday = day.weekday()
    if days_to_race == 0:
        return {
            "date": day.isoformat(),
            "type": "race",
            "title": "Полумарафон",
            "instructions": "Первые 3-5 км спокойно, затем держать ровное усилие. Цель sub-2: около 5:41/км, но пульс и состояние важнее.",
        }
    if days_to_race == 1:
        return {
            "date": day.isoformat(),
            "type": "rest",
            "title": "Отдых перед стартом",
            "instructions": "Без тренировки или 15-20 минут прогулки. Подготовить экипировку и питание.",
        }
    if days_to_race == 2:
        return {
            "date": day.isoformat(),
            "type": "shakeout",
            "title": "Короткая разминка",
            "instructions": "20-25 минут очень легко + 3 коротких ускорения по 15-20 секунд, если ноги свежие.",
        }
    if days_to_race in {3, 4}:
        return {
            "date": day.isoformat(),
            "type": "easy_run" if weekday in {1, 3} else "rest",
            "title": "Лёгкая поддержка",
            "instructions": "Если бежишь: 30-40 минут легко, без набора усталости. Если есть тяжесть - отдых.",
        }
    if days_to_race == 8:
        return {
            "date": day.isoformat(),
            "type": "race_pace",
            "title": "Короткая работа в целевом усилии",
            "instructions": "Разминка 15 минут, затем 3 x 2 км около темпа полумарафона с лёгким восстановлением, заминка 10 минут. Не добивать.",
        }
    if days_to_race == 7:
        return {
            "date": day.isoformat(),
            "type": "rest",
            "title": "Восстановление после работы",
            "instructions": "Отдых, прогулка или мягкая мобилизация. Без силовой на ноги.",
        }
    if days_to_race == 6:
        return {
            "date": day.isoformat(),
            "type": "long_easy",
            "title": "Последняя спокойная длительная",
            "instructions": "70-80 минут легко. Без финишного ускорения, задача - тонус, не усталость.",
        }
    if weekday == 6:
        return {
            "date": day.isoformat(),
            "type": "long_easy",
            "title": "Последняя спокойная длительная",
            "instructions": "70-85 минут легко. Без финишного ускорения, задача - тонус, не усталость.",
        }
    if weekday in {1, 3}:
        return {
            "date": day.isoformat(),
            "type": "easy_run",
            "title": "Лёгкий бег",
            "instructions": "35-50 минут в разговорном темпе. Контроль пульса и ощущения 3-4/10.",
        }
    return {
        "date": day.isoformat(),
        "type": "rest",
        "title": "Отдых или мобилизация",
        "instructions": "Прогулка, сон, мягкая мобилизация. Без тяжёлой силовой на ноги.",
    }


def _format_longest(workouts: list[dict[str, Any]]) -> list[str]:
    return [f"{item['date']} - {item['distance_km']} км" for item in workouts if item.get("distance_km")]
