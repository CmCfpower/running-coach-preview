"""Workout extraction from raw screenshots."""

from __future__ import annotations

import base64
import json
import mimetypes
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from running_coach.llm import OpenAICompatibleClient
from running_coach.storage import ProjectStorage


WORKOUT_FIELDS = {
    "sport",
    "distance_km",
    "duration_sec",
    "avg_pace_sec_per_km",
    "avg_hr",
    "max_hr",
    "elevation_gain_m",
    "cadence_spm",
    "rpe",
    "extraction_confidence",
}


@dataclass(frozen=True)
class ExtractionResult:
    date: str
    parsed_path: str
    updated: bool
    confidence: float
    images_read: int


def extract_workout_from_images(
    storage: ProjectStorage,
    workout_date: str,
    client: OpenAICompatibleClient,
    *,
    prompt_path: str | Path,
    max_images: int = 4,
    force: bool = False,
    prefer_recent: bool = False,
) -> ExtractionResult:
    parsed_relative = f"data/workouts/{workout_date}/parsed.json"
    record = storage.read_json(parsed_relative)
    confidence = float(record.get("extraction_confidence") or 0)
    if not _needs_extraction(record) and not force:
        return ExtractionResult(workout_date, parsed_relative, False, confidence, 0)

    raw_files = [storage.resolve(path) for path in record.get("raw_files", [])]
    selected_images = raw_files[-max_images:] if prefer_recent else raw_files[:max_images]
    if not selected_images:
        raise FileNotFoundError(f"No raw files for workout date: {workout_date}")

    prompt = Path(prompt_path).read_text(encoding="utf-8")
    response = client.chat(
        [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Extract one primary workout from these screenshots. "
                            "Return JSON only. Keep unknown fields null. "
                            f"Date from storage: {workout_date}. "
                            f"Existing raw_files: {record.get('raw_files', [])}"
                        ),
                    },
                    *[_image_part(path) for path in selected_images],
                ],
            },
        ]
    )
    extracted = _parse_json_response(response)
    extracted_date = _valid_date(extracted.get("date")) or workout_date
    if extracted_date != workout_date:
        merged, parsed_relative = _relocate_extracted_record(
            storage,
            record=record,
            extracted=extracted,
            source_date=workout_date,
            target_date=extracted_date,
        )
    else:
        merged = _merge_extracted_record(record, extracted, workout_date)
        storage.write_json(parsed_relative, merged)
    return ExtractionResult(
        extracted_date,
        parsed_relative,
        True,
        float(merged.get("extraction_confidence") or 0),
        len(selected_images),
    )


def _image_part(path: Path) -> dict[str, Any]:
    mime_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return {
        "type": "image_url",
        "image_url": {
            "url": f"data:{mime_type};base64,{data}",
        },
    }


def _parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    try:
        value = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM did not return valid JSON: {text[:500]}") from exc
    if not isinstance(value, dict):
        raise ValueError("LLM response must be a JSON object.")
    return value


def _merge_extracted_record(existing: dict[str, Any], extracted: dict[str, Any], workout_date: str) -> dict[str, Any]:
    merged = dict(existing)
    merged["id"] = f"{workout_date}-run-001"
    merged["date"] = workout_date
    merged["source"] = existing.get("source", "history")
    merged["raw_files"] = list(existing.get("raw_files", []))

    for field in WORKOUT_FIELDS:
        if field not in extracted:
            continue
        value = extracted[field]
        if value is not None:
            merged[field] = _normalize_field(field, value)

    notes = list(existing.get("notes", []))
    for note in extracted.get("notes", []):
        if isinstance(note, str) and note not in notes:
            notes.append(note)
    if _derive_distance_from_pace(merged):
        notes.append("Distance derived from duration and average pace.")
    extraction_note = "Workout values extracted from raw screenshots by vision LLM."
    if extraction_note not in notes:
        notes.append(extraction_note)
    merged["notes"] = notes
    merged["extraction_confidence"] = _bounded_confidence(merged)
    return merged


def _relocate_extracted_record(
    storage: ProjectStorage,
    *,
    record: dict[str, Any],
    extracted: dict[str, Any],
    source_date: str,
    target_date: str,
) -> tuple[dict[str, Any], str]:
    target_relative = f"data/workouts/{target_date}/parsed.json"
    target_path = storage.resolve(target_relative)
    if target_path.exists():
        target_record = storage.read_json(target_relative)
    else:
        target_record = {
            **record,
            "id": f"{target_date}-run-001",
            "date": target_date,
            "raw_files": [],
            "raw_file_hashes": {},
            "notes": [],
        }

    target_record = dict(target_record)
    source_raw_files = list(record.get("raw_files", []))
    target_raw_files = list(target_record.get("raw_files", []))
    target_hashes = dict(target_record.get("raw_file_hashes", {}))
    source_hashes = dict(record.get("raw_file_hashes", {}))

    for raw_file in source_raw_files:
        raw_hash = source_hashes.get(raw_file)
        duplicate = raw_hash and raw_hash in set(target_hashes.values())
        if duplicate:
            continue

        source_path = storage.resolve(raw_file)
        if not source_path.exists():
            continue
        target_raw_dir = storage.ensure_dir("data", "workouts", target_date, "raw")
        target_raw_path = _next_unique_path(target_raw_dir, source_path.name)
        source_path.replace(target_raw_path)
        target_raw_relative = storage.relative(target_raw_path)
        target_raw_files.append(target_raw_relative)
        if raw_hash:
            target_hashes[target_raw_relative] = raw_hash

    target_record["raw_files"] = target_raw_files
    target_record["raw_file_hashes"] = target_hashes
    notes = list(target_record.get("notes", []))
    relocation_note = f"Relocated from {source_date} after screenshot date extraction."
    if relocation_note not in notes:
        notes.append(relocation_note)
    target_record["notes"] = notes

    merged = _merge_extracted_record(target_record, extracted, target_date)
    storage.write_json(target_relative, merged)

    source_note = f"Ignored: workout date was extracted as {target_date}."
    ignored = dict(record)
    notes = list(ignored.get("notes", []))
    if source_note not in notes:
        notes.append(source_note)
    ignored["notes"] = notes
    storage.write_json(f"data/workouts/{source_date}/parsed.json", ignored)
    return merged, target_relative


def _normalize_field(field: str, value: Any) -> Any:
    if field in {"duration_sec", "avg_pace_sec_per_km"}:
        return _parse_seconds(value)
    if field in {"avg_hr", "max_hr", "cadence_spm"}:
        return int(round(float(value)))
    if field in {"distance_km", "elevation_gain_m", "rpe", "extraction_confidence"}:
        return _parse_float(value)
    return value


def _parse_seconds(value: Any) -> int:
    if isinstance(value, str) and ":" in value:
        parts = [int(part) for part in value.strip().split(":")]
        if len(parts) == 2:
            minutes, seconds = parts
            return minutes * 60 + seconds
        if len(parts) == 3:
            hours, minutes, seconds = parts
            return hours * 3600 + minutes * 60 + seconds
    return int(round(float(value)))


def _parse_float(value: Any) -> float:
    if isinstance(value, str):
        match = re.search(r"-?\d+(?:[.,]\d+)?", value)
        if not match:
            raise ValueError(f"Cannot parse numeric value: {value!r}")
        value = match.group(0).replace(",", ".")
    return float(value)


def _bounded_confidence(record: dict[str, Any]) -> float:
    confidence = float(record.get("extraction_confidence") or 0)
    notes = record.get("notes", [])
    if "Distance derived from duration and average pace." in notes:
        confidence = min(confidence, 0.85)
    required_fields = ("distance_km", "duration_sec", "avg_pace_sec_per_km")
    present_required = sum(record.get(field) is not None for field in required_fields)

    if present_required == 0:
        return min(confidence, 0.2)
    if present_required == 1:
        return min(confidence, 0.45)
    if present_required == 2:
        return min(confidence, 0.75)
    return min(confidence, 1.0)


def _derive_distance_from_pace(record: dict[str, Any]) -> bool:
    if record.get("distance_km") is not None:
        return False
    duration = record.get("duration_sec")
    pace = record.get("avg_pace_sec_per_km")
    if duration is None or pace in (None, 0):
        return False
    distance = float(duration) / float(pace)
    if distance <= 0:
        return False
    record["distance_km"] = round(distance, 2)
    return True


def _valid_date(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value[:10]).isoformat()
    except ValueError:
        return None


def _next_unique_path(directory: Path, filename: str) -> Path:
    candidate = directory / filename
    if not candidate.exists():
        return candidate
    stem = candidate.stem
    suffix = candidate.suffix
    counter = 2
    while True:
        candidate = directory / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def _needs_extraction(record: dict[str, Any]) -> bool:
    if not record.get("extraction_confidence"):
        return True
    notes = record.get("notes") or []
    if isinstance(notes, list):
        extraction_attempts = sum(
            note == "Workout values extracted from raw screenshots by vision LLM." for note in notes
        )
        if extraction_attempts >= 2:
            return False
    required_fields = ("distance_km", "duration_sec", "avg_pace_sec_per_km")
    return any(record.get(field) is None for field in required_fields)
