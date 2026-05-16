from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from running_coach.config import load_project_config
from running_coach.services.workouts import import_workout_file
from running_coach.storage import ProjectStorage


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Import a workout screenshot into local storage.")
    parser.add_argument("date", help="Workout date in YYYY-MM-DD format.")
    parser.add_argument("file", help="Path to the source workout screenshot/file.")
    parser.add_argument("--source", default="telegram", help="Source label, default: telegram.")
    parser.add_argument("--caption", default=None, help="Optional user caption/note.")
    args = parser.parse_args()

    config = load_project_config(ROOT / "project.yaml")
    storage = ProjectStorage(config.root)
    result = import_workout_file(
        storage,
        args.date,
        args.file,
        source=args.source,
        caption=args.caption,
    )

    print("Workout imported")
    print(f"ID: {result.workout_id}")
    print(f"Date: {result.date}")
    print(f"Raw file: {result.raw_file}")
    print(f"Parsed JSON: {result.parsed_path}")
    print(f"Created parsed record: {result.created}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
