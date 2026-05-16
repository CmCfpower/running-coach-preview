"""Workout ingestion service."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from running_coach.storage import ProjectStorage


@dataclass(frozen=True)
class WorkoutImportResult:
    workout_id: str
    date: str
    raw_file: str
    parsed_path: str
    created: bool
    duplicate: bool = False


def load_workout_for_date(storage: ProjectStorage, workout_date: str) -> dict[str, Any] | None:
    """Load a parsed workout record for a date when one exists."""

    path = storage.resolve("data", "workouts", workout_date, "parsed.json")
    if not path.exists():
        return None
    record = storage.read_json("data", "workouts", workout_date, "parsed.json")
    notes = record.get("notes") or []
    if any(isinstance(note, str) and note.startswith("Ignored:") for note in notes):
        return None
    return record


def format_workout_fact(record: dict[str, Any]) -> str:
    """Format a short actual-workout summary for Telegram."""

    parts = ["Факт: тренировка записана"]
    distance = record.get("distance_km")
    duration = record.get("duration_sec")
    pace = record.get("avg_pace_sec_per_km")
    avg_hr = record.get("avg_hr")

    details: list[str] = []
    if distance is not None:
        details.append(f"{distance:g} км")
    if duration is not None:
        details.append(_format_duration(duration))
    if pace is not None:
        details.append(f"темп {_format_pace(pace)}/км")
    if avg_hr is not None:
        details.append(f"пульс {avg_hr}")

    if details:
        parts.append(", ".join(details))

    confidence = record.get("extraction_confidence")
    if confidence is not None:
        parts.append(f"уверенность {float(confidence):.2f}")

    return "\n".join(parts)


def format_workout_analysis(
    record: dict[str, Any],
    day_plan: dict[str, Any] | None = None,
) -> str:
    distance = record.get("distance_km")
    duration = record.get("duration_sec")
    pace = record.get("avg_pace_sec_per_km")
    avg_hr = record.get("avg_hr")

    lines = ["Анализ тренировки:"]
    if distance is not None and duration is not None:
        lines.append(f"- Объем: {distance:g} км за {_format_duration(duration)}.")
    if pace is not None:
        lines.append(f"- Средний темп: {_format_pace(pace)}/км.")
    if avg_hr is not None:
        lines.append(f"- Средний пульс: {avg_hr}.")
    else:
        lines.append("- Пульса нет в данных, поэтому оценка интенсивности неполная.")

    planned_type = day_plan.get("type") if day_plan else None
    if planned_type == "rest" and distance:
        lines.append("- По плану был отдых: считаю это дополнительной нагрузкой.")
    elif planned_type:
        lines.append(f"- План дня: {planned_type}. Сверяю факт с назначением.")

    if distance is not None:
        if distance < 4:
            lines.append("- Нагрузка короткая, ближе к восстановительной.")
        elif distance <= 9:
            lines.append("- Нагрузка умеренная; важно не добавлять лишнюю интенсивность следом.")
        else:
            lines.append("- Нагрузка заметная; следующий день лучше планировать осторожно.")

    return "\n".join(lines)


def import_workout_file(
    storage: ProjectStorage,
    workout_date: str,
    source_file: str | Path,
    *,
    source: str = "telegram",
    caption: str | None = None,
) -> WorkoutImportResult:
    """Copy a workout file into project storage and create/update parsed.json."""

    source_hash = _sha256_file(Path(source_file))
    global_duplicate = _find_existing_workout_by_raw_hash(storage, source_hash)
    if global_duplicate is not None:
        duplicate_date, duplicate_raw, duplicate_record = global_duplicate
        return WorkoutImportResult(
            workout_id=str(duplicate_record["id"]),
            date=duplicate_date,
            raw_file=duplicate_raw,
            parsed_path=f"data/workouts/{duplicate_date}/parsed.json",
            created=False,
            duplicate=True,
        )

    paths = storage.workout_paths(workout_date)
    parsed_relative = storage.relative(paths.parsed_json)
    existing = _load_existing_parsed(storage, parsed_relative)
    created = existing is None
    record = existing or _draft_workout_record(workout_date, source)

    raw_hashes = dict(record.get("raw_file_hashes", {}))
    duplicate_raw = _find_duplicate_raw(raw_hashes, source_hash)
    if duplicate_raw is not None:
        storage.write_json(parsed_relative, record)
        return WorkoutImportResult(
            workout_id=str(record["id"]),
            date=workout_date,
            raw_file=duplicate_raw,
            parsed_path=parsed_relative,
            created=created,
            duplicate=True,
        )

    extension = Path(source_file).suffix.lstrip(".") or "bin"
    raw_path = storage.next_raw_workout_path(workout_date, source, extension)
    copied = storage.copy_file_into_project(source_file, storage.relative(raw_path))
    raw_relative = storage.relative(copied)

    raw_files = list(record.get("raw_files", []))
    if raw_relative not in raw_files:
        raw_files.append(raw_relative)
    record["raw_files"] = raw_files
    raw_hashes[raw_relative] = source_hash
    record["raw_file_hashes"] = raw_hashes
    record["source"] = source

    notes = list(record.get("notes", []))
    if caption:
        notes.append(caption)
    record["notes"] = notes

    storage.write_json(parsed_relative, record)

    return WorkoutImportResult(
        workout_id=str(record["id"]),
        date=workout_date,
        raw_file=raw_relative,
        parsed_path=parsed_relative,
        created=created,
        duplicate=False,
    )


def _load_existing_parsed(storage: ProjectStorage, relative_path: str) -> dict[str, Any] | None:
    path = storage.resolve(relative_path)
    if not path.exists():
        return None
    record = storage.read_json(relative_path)
    if _is_ignored_record(record):
        return None
    return record


def _find_existing_workout_by_raw_hash(
    storage: ProjectStorage,
    source_hash: str,
) -> tuple[str, str, dict[str, Any]] | None:
    workouts_dir = storage.resolve("data", "workouts")
    if not workouts_dir.exists():
        return None

    for parsed_path in sorted(workouts_dir.glob("*/parsed.json")):
        record = storage.read_json(storage.relative(parsed_path))
        if _is_ignored_record(record):
            continue
        duplicate_raw = _find_duplicate_raw(dict(record.get("raw_file_hashes", {})), source_hash)
        if duplicate_raw is None:
            continue
        record_date = str(record.get("date") or parsed_path.parent.name)
        return record_date, duplicate_raw, record
    return None


def _is_ignored_record(record: dict[str, Any]) -> bool:
    notes = record.get("notes") or []
    return any(isinstance(note, str) and note.startswith("Ignored:") for note in notes)


def _draft_workout_record(workout_date: str, source: str) -> dict[str, Any]:
    return {
        "id": f"{workout_date}-run-001",
        "date": workout_date,
        "source": source,
        "raw_files": [],
        "raw_file_hashes": {},
        "sport": "running",
        "distance_km": None,
        "duration_sec": None,
        "avg_pace_sec_per_km": None,
        "avg_hr": None,
        "max_hr": None,
        "elevation_gain_m": None,
        "cadence_spm": None,
        "rpe": None,
        "extraction_confidence": 0,
        "notes": [
            f"Draft record created at {datetime.now().isoformat(timespec='seconds')}.",
            "Workout values are not extracted yet.",
        ],
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _find_duplicate_raw(raw_hashes: dict[str, str], source_hash: str) -> str | None:
    for raw_file, existing_hash in raw_hashes.items():
        if existing_hash == source_hash:
            return raw_file
    return None


def _format_duration(seconds: int | float) -> str:
    seconds_int = int(seconds)
    hours, rest = divmod(seconds_int, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _format_pace(seconds: int | float) -> str:
    minutes, rest = divmod(int(seconds), 60)
    return f"{minutes}:{rest:02d}"
