from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(sys.executable)
sys.path.insert(0, str(ROOT / "scripts"))

from check_bot_status import cleanup_stale_pid, get_bot_status


def main() -> int:
    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)

    status = get_bot_status()
    if status.status == "running":
        print(f"Bot already running. PID={status.pid}")
        return 0
    if status.status == "stale_pid":
        cleanup_stale_pid(status)
        print(f"Removed stale PID file for PID={status.pid}")

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"

    stdout = (logs / "bot_stdout.log").open("ab")
    stderr = (logs / "bot_stderr.log").open("ab")
    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP

    process = subprocess.Popen(
        [str(PYTHON), "scripts/run_running_bot.py"],
        cwd=ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
        creationflags=creationflags,
    )
    (logs / "bot.pid").write_text(str(process.pid), encoding="ascii")
    print(f"Bot started. PID={process.pid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
