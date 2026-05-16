from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from running_coach.bot.running_bot import build_running_bot
from running_coach.config import load_project_config
from running_coach.env import load_dotenv
from running_coach.storage import ProjectStorage


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    logs_dir = ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        filename=logs_dir / "running_bot.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)

    load_dotenv(ROOT / ".env")
    config = load_project_config(ROOT / "project.yaml")
    storage = ProjectStorage(config.root)
    app = build_running_bot(config, storage)
    print("Running bot started. Press Ctrl+C to stop.")
    app.run_polling()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
