from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from running_coach.config import load_project_config
from running_coach.services.profile import format_profile_summary, load_profile
from running_coach.services.training_plan import (
    find_day_plan,
    format_day_plan,
    load_current_training_plan,
)
from running_coach.storage import ProjectStorage


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    target_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    config = load_project_config(ROOT / "project.yaml")
    storage = ProjectStorage(config.root)

    profile = load_profile(storage)
    plan = load_current_training_plan(storage)
    day_plan = find_day_plan(plan, target_date)

    print(format_profile_summary(profile))
    print()
    print(format_day_plan(day_plan, target_date))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
