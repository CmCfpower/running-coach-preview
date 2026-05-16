from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from running_coach.config import load_project_config
from running_coach.env import load_dotenv
from running_coach.llm import OpenAICompatibleClient, build_client_from_env
from running_coach.services.workout_extraction import extract_workout_from_images
from running_coach.storage import ProjectStorage


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Extract structured workout values from raw screenshots.")
    parser.add_argument("--date", help="Extract one workout date, YYYY-MM-DD.")
    parser.add_argument("--limit", type=int, default=3, help="Maximum workout dates to process.")
    parser.add_argument("--max-images", type=int, default=4, help="Maximum images sent per workout date.")
    parser.add_argument("--prefer-recent", action="store_true", help="Use the most recent raw images first.")
    parser.add_argument("--force", action="store_true", help="Re-extract workouts with existing confidence.")
    parser.add_argument("--dry-run", action="store_true", help="Show selected dates without calling the LLM.")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    config = load_project_config(ROOT / "project.yaml")
    storage = ProjectStorage(config.root)

    dates = [args.date] if args.date else _candidate_dates(storage, limit=args.limit, force=args.force)
    if args.dry_run:
        print("Dates selected:")
        for workout_date in dates:
            print(f"- {workout_date}")
        return 0

    client = build_client_from_env(vision=True)
    for workout_date in dates:
        result = extract_workout_from_images(
            storage,
            workout_date,
            client,
            prompt_path=ROOT / "prompts" / "workout_extract.md",
            max_images=args.max_images,
            force=args.force,
            prefer_recent=args.prefer_recent,
        )
        status = "updated" if result.updated else "skipped"
        print(f"{workout_date}: {status}, confidence={result.confidence:.2f}, path={result.parsed_path}")
    return 0


def _candidate_dates(storage: ProjectStorage, *, limit: int, force: bool) -> list[str]:
    root = storage.resolve("data/workouts")
    dates: list[str] = []
    for parsed_path in sorted(root.glob("*/parsed.json")):
        record = storage.read_json(storage.relative(parsed_path))
        if force or _needs_extraction(record):
            dates.append(parsed_path.parent.name)
        if len(dates) >= limit:
            break
    return dates


def _needs_extraction(record: dict[str, object]) -> bool:
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

if __name__ == "__main__":
    raise SystemExit(main())
