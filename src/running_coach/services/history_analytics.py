"""History aggregation for parsed workouts."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any

from running_coach.storage import ProjectStorage


CORE_FIELDS = ("distance_km", "duration_sec", "avg_pace_sec_per_km")


@dataclass(frozen=True)
class HistoryAggregation:
    summary: dict[str, Any]
    markdown: str


def aggregate_history(storage: ProjectStorage, *, today: date | None = None) -> HistoryAggregation:
    today = today or date.today()
    workouts = _load_workouts(storage)
    complete = [workout for workout in workouts if _has_core_fields(workout)]
    suspicious = [workout for workout in complete if _is_suspicious(workout)]
    analysis_ready = [workout for workout in complete if not _is_suspicious(workout)]
    partial = [workout for workout in workouts if not _has_core_fields(workout)]

    weekly = _weekly_stats(analysis_ready)
    recent_4_weeks = _recent_weeks(weekly, today=today, weeks=4)
    recent_6_weeks = _recent_weeks(weekly, today=today, weeks=6)

    summary = {
        "generated_at": today.isoformat(),
        "total_records": len(workouts),
        "complete_records": len(complete),
        "analysis_records": len(analysis_ready),
        "partial_records": len(partial),
        "suspicious_records": len(suspicious),
        "date_range": _date_range(workouts),
        "totals": _totals(analysis_ready),
        "recent_4_weeks": _rollup_weeks(recent_4_weeks),
        "recent_6_weeks": _rollup_weeks(recent_6_weeks),
        "weekly": weekly,
        "longest_workouts": _longest_workouts(analysis_ready, limit=10),
        "recent_workouts": _recent_workouts(analysis_ready, limit=14),
        "partial_workouts": [_partial_summary(workout) for workout in partial],
        "suspicious_workouts": [_suspicious_summary(workout) for workout in suspicious],
    }
    return HistoryAggregation(summary=summary, markdown=_to_markdown(summary))


def _load_workouts(storage: ProjectStorage) -> list[dict[str, Any]]:
    root = storage.resolve("data/workouts")
    workouts = []
    for parsed_path in sorted(root.glob("*/parsed.json")):
        workout = storage.read_json(storage.relative(parsed_path))
        workouts.append(workout)
    return sorted(workouts, key=lambda item: item["date"])


def _has_core_fields(workout: dict[str, Any]) -> bool:
    return all(workout.get(field) is not None for field in CORE_FIELDS)


def _is_suspicious(workout: dict[str, Any]) -> bool:
    pace = workout.get("avg_pace_sec_per_km")
    duration = workout.get("duration_sec")
    distance = workout.get("distance_km")
    if distance is not None and float(distance) <= 0:
        return True
    if pace is not None and (int(pace) < 180 or int(pace) > 1200):
        return True
    if duration is not None and int(duration) > 6 * 3600:
        return True
    return False


def _weekly_stats(workouts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for workout in workouts:
        workout_date = date.fromisoformat(workout["date"])
        week_start = workout_date - timedelta(days=workout_date.weekday())
        buckets[week_start.isoformat()].append(workout)

    weeks = []
    for week_start, week_workouts in sorted(buckets.items()):
        weeks.append(
            {
                "week_start": week_start,
                "week_end": (date.fromisoformat(week_start) + timedelta(days=6)).isoformat(),
                **_rollup(week_workouts),
                "longest_distance_km": _max_number(week_workouts, "distance_km"),
                "longest_duration_sec": _max_number(week_workouts, "duration_sec"),
            }
        )
    return weeks


def _recent_weeks(weekly: list[dict[str, Any]], *, today: date, weeks: int) -> list[dict[str, Any]]:
    current_week_start = today - timedelta(days=today.weekday())
    min_week_start = current_week_start - timedelta(days=7 * (weeks - 1))
    return [
        week
        for week in weekly
        if date.fromisoformat(week["week_start"]) >= min_week_start
        and date.fromisoformat(week["week_start"]) <= current_week_start
    ]


def _rollup(items: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(items)
    distance = sum(float(item.get("distance_km") or 0) for item in items)
    duration = sum(int(item.get("duration_sec") or 0) for item in items)
    avg_pace = round(duration / distance) if distance > 0 else None
    return {
        "workout_count": count,
        "distance_km": round(distance, 2),
        "duration_sec": duration,
        "avg_pace_sec_per_km": avg_pace,
    }


def _rollup_weeks(weeks: list[dict[str, Any]]) -> dict[str, Any]:
    workout_count = sum(int(week.get("workout_count") or 0) for week in weeks)
    distance = sum(float(week.get("distance_km") or 0) for week in weeks)
    duration = sum(int(week.get("duration_sec") or 0) for week in weeks)
    avg_pace = round(duration / distance) if distance > 0 else None
    return {
        "week_count": len(weeks),
        "workout_count": workout_count,
        "distance_km": round(distance, 2),
        "duration_sec": duration,
        "avg_pace_sec_per_km": avg_pace,
    }


def _totals(workouts: list[dict[str, Any]]) -> dict[str, Any]:
    totals = _rollup(workouts)
    if workouts:
        totals["avg_distance_km"] = round(totals["distance_km"] / len(workouts), 2)
        totals["avg_duration_sec"] = round(totals["duration_sec"] / len(workouts))
    else:
        totals["avg_distance_km"] = None
        totals["avg_duration_sec"] = None
    return totals


def _longest_workouts(workouts: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    return [
        _workout_summary(workout)
        for workout in sorted(workouts, key=lambda item: float(item.get("distance_km") or 0), reverse=True)[:limit]
    ]


def _recent_workouts(workouts: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    return [_workout_summary(workout) for workout in sorted(workouts, key=lambda item: item["date"], reverse=True)[:limit]]


def _workout_summary(workout: dict[str, Any]) -> dict[str, Any]:
    return {
        "date": workout["date"],
        "distance_km": workout.get("distance_km"),
        "duration_sec": workout.get("duration_sec"),
        "avg_pace_sec_per_km": workout.get("avg_pace_sec_per_km"),
        "avg_hr": workout.get("avg_hr"),
        "elevation_gain_m": workout.get("elevation_gain_m"),
        "confidence": workout.get("extraction_confidence"),
    }


def _partial_summary(workout: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in CORE_FIELDS if workout.get(field) is None]
    return {
        "date": workout["date"],
        "missing": missing,
        "available": {
            "distance_km": workout.get("distance_km"),
            "duration_sec": workout.get("duration_sec"),
            "avg_pace_sec_per_km": workout.get("avg_pace_sec_per_km"),
        },
        "confidence": workout.get("extraction_confidence"),
    }


def _suspicious_summary(workout: dict[str, Any]) -> dict[str, Any]:
    reasons = []
    pace = workout.get("avg_pace_sec_per_km")
    duration = workout.get("duration_sec")
    distance = workout.get("distance_km")
    if distance is not None and float(distance) <= 0:
        reasons.append("non_positive_distance")
    if pace is not None and (int(pace) < 180 or int(pace) > 1200):
        reasons.append("implausible_pace")
    if duration is not None and int(duration) > 6 * 3600:
        reasons.append("implausible_duration")
    return {**_workout_summary(workout), "reasons": reasons}


def _date_range(workouts: list[dict[str, Any]]) -> dict[str, str | None]:
    if not workouts:
        return {"start": None, "end": None}
    return {"start": workouts[0]["date"], "end": workouts[-1]["date"]}


def _max_number(workouts: list[dict[str, Any]], field: str) -> float | int | None:
    values = [workout.get(field) for workout in workouts if workout.get(field) is not None]
    return max(values) if values else None


def _to_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Running History Summary",
        "",
        f"Generated at: {summary['generated_at']}",
        f"Date range: {summary['date_range']['start']} - {summary['date_range']['end']}",
        f"Records: {summary['analysis_records']} analysis-ready / {summary['total_records']} total",
        "",
        "## Totals",
        "",
        f"- Workouts: {summary['totals']['workout_count']}",
        f"- Distance: {summary['totals']['distance_km']} km",
        f"- Duration: {_format_duration(summary['totals']['duration_sec'])}",
        f"- Average pace: {_format_pace(summary['totals']['avg_pace_sec_per_km'])}",
        "",
        "## Recent 4 Weeks",
        "",
        f"- Workouts: {summary['recent_4_weeks']['workout_count']}",
        f"- Distance: {summary['recent_4_weeks']['distance_km']} km",
        f"- Average pace: {_format_pace(summary['recent_4_weeks']['avg_pace_sec_per_km'])}",
        "",
        "## Weekly",
        "",
        "| Week | Workouts | Distance | Avg pace | Longest |",
        "|---|---:|---:|---:|---:|",
    ]
    for week in summary["weekly"]:
        lines.append(
            "| "
            f"{week['week_start']} | "
            f"{week['workout_count']} | "
            f"{week['distance_km']} km | "
            f"{_format_pace(week['avg_pace_sec_per_km'])} | "
            f"{week['longest_distance_km']} km |"
        )

    lines.extend(["", "## Longest Workouts", ""])
    for workout in summary["longest_workouts"]:
        lines.append(
            f"- {workout['date']}: {workout['distance_km']} km, "
            f"{_format_duration(workout['duration_sec'])}, {_format_pace(workout['avg_pace_sec_per_km'])}"
        )

    if summary["partial_workouts"]:
        lines.extend(["", "## Manual Review", ""])
        for workout in summary["partial_workouts"]:
            lines.append(
                f"- {workout['date']}: missing {', '.join(workout['missing'])}, "
                f"confidence {workout['confidence']}"
            )
    if summary["suspicious_workouts"]:
        if not summary["partial_workouts"]:
            lines.extend(["", "## Manual Review", ""])
        for workout in summary["suspicious_workouts"]:
            lines.append(
                f"- {workout['date']}: suspicious {', '.join(workout['reasons'])}, "
                f"{workout['distance_km']} km, {_format_duration(workout['duration_sec'])}, "
                f"{_format_pace(workout['avg_pace_sec_per_km'])}"
            )
    lines.append("")
    return "\n".join(lines)


def _format_duration(seconds: int | None) -> str:
    if seconds is None:
        return "-"
    hours, remainder = divmod(int(seconds), 3600)
    minutes, sec = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{sec:02d}"
    return f"{minutes}:{sec:02d}"


def _format_pace(seconds: int | None) -> str:
    if seconds is None:
        return "-"
    minutes, sec = divmod(int(seconds), 60)
    return f"{minutes}:{sec:02d}/km"
