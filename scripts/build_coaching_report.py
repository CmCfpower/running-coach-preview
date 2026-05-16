from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from running_coach.config import load_project_config
from running_coach.services.coaching_report import build_half_marathon_report, to_markdown
from running_coach.storage import ProjectStorage


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Build coaching report and race-week plan.")
    parser.add_argument("--today", default=date.today().isoformat(), help="Analysis date, YYYY-MM-DD.")
    parser.add_argument("--race-date", default="2026-05-23", help="Race date, YYYY-MM-DD.")
    args = parser.parse_args()

    config = load_project_config(ROOT / "project.yaml")
    storage = ProjectStorage(config.root)
    history = storage.read_json("data/derived/history_summary.json")
    report = build_half_marathon_report(
        history,
        today=date.fromisoformat(args.today),
        race_date=date.fromisoformat(args.race_date),
    )

    report_path = storage.write_json("data/derived/coaching_report.json", report)
    plan_path = storage.write_json("data/derived/current_training_plan.json", _training_plan_from_report(report))
    markdown_path = storage.resolve("reports/coaching_report.md")
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(to_markdown(report), encoding="utf-8")

    print(f"Readiness: {report['readiness']['status']}")
    print(f"Days to race: {report['days_to_race']}")
    print(f"Plan days: {len(report['plan']['days'])}")
    print(f"JSON: {storage.relative(report_path)}")
    print(f"Plan: {storage.relative(plan_path)}")
    print(f"Markdown: {storage.relative(markdown_path)}")
    return 0


def _training_plan_from_report(report: dict) -> dict:
    return {
        "week_start": report["generated_at"],
        "week_end": report["race_date"],
        "generated_at": report["generated_at"],
        "summary": (
            "План до асфальтового полумарафона 23 мая. "
            "Фокус: свежесть, лёгкое поддержание формы, контроль пульса."
        ),
        "days": [
            {
                "date": day["date"],
                "type": day["type"],
                "duration_min": None,
                "distance_km": None,
                "target_hr_min": None,
                "target_hr_max": None,
                "target_pace_min_sec_per_km": None,
                "target_pace_max_sec_per_km": None,
                "instructions": f"{day['title']}. {day['instructions']}",
                "warnings": [],
            }
            for day in report["plan"]["days"]
        ],
        "warnings": report["risks"],
    }


if __name__ == "__main__":
    raise SystemExit(main())
