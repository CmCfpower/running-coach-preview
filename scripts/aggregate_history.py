from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from running_coach.config import load_project_config
from running_coach.services.history_analytics import aggregate_history
from running_coach.storage import ProjectStorage


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Aggregate parsed running workout history.")
    parser.add_argument("--today", default=date.today().isoformat(), help="Analysis date, YYYY-MM-DD.")
    args = parser.parse_args()

    config = load_project_config(ROOT / "project.yaml")
    storage = ProjectStorage(config.root)
    result = aggregate_history(storage, today=date.fromisoformat(args.today))

    json_path = storage.write_json("data/derived/history_summary.json", result.summary)
    md_path = storage.resolve("reports/history_summary.md")
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(result.markdown, encoding="utf-8")

    totals = result.summary["totals"]
    recent = result.summary["recent_4_weeks"]
    print(f"Records: {result.summary['analysis_records']} analysis-ready / {result.summary['total_records']} total")
    print(f"Total distance: {totals['distance_km']} km")
    print(f"Recent 4 weeks: {recent['distance_km']} km across {recent['workout_count']} workouts")
    print(f"Partial records: {result.summary['partial_records']}")
    print(f"Suspicious records: {result.summary['suspicious_records']}")
    print(f"JSON: {storage.relative(json_path)}")
    print(f"Markdown: {storage.relative(md_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
