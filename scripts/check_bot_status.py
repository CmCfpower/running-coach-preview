from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PID_FILE = ROOT / "logs" / "bot.pid"
LOG_FILE = ROOT / "logs" / "running_bot.log"


@dataclass(frozen=True)
class BotStatus:
    status: str
    pid: int | None
    pid_file: str
    pid_file_exists: bool
    process_alive: bool
    log_file: str
    log_file_exists: bool
    log_updated_at: str | None
    checked_at: str
    message: str


def get_bot_status() -> BotStatus:
    pid = _read_pid(PID_FILE)
    process_alive = _is_process_alive(pid) if pid is not None else False
    log_updated_at = _mtime_iso(LOG_FILE)

    if pid is not None and process_alive:
        status = "running"
        message = f"Bot is running. PID={pid}"
    elif pid is not None:
        status = "stale_pid"
        message = f"PID file exists but process is not alive. PID={pid}"
    else:
        status = "down"
        message = "Bot is not running and PID file is missing or invalid."

    return BotStatus(
        status=status,
        pid=pid,
        pid_file=_rel(PID_FILE),
        pid_file_exists=PID_FILE.exists(),
        process_alive=process_alive,
        log_file=_rel(LOG_FILE),
        log_file_exists=LOG_FILE.exists(),
        log_updated_at=log_updated_at,
        checked_at=datetime.now(timezone.utc).isoformat(),
        message=message,
    )


def cleanup_stale_pid(status: BotStatus | None = None) -> bool:
    status = status or get_bot_status()
    if status.status != "stale_pid":
        return False
    PID_FILE.unlink(missing_ok=True)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Running Coach Telegram bot status.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--cleanup-stale", action="store_true", help="Remove stale PID file.")
    args = parser.parse_args()

    status = get_bot_status()
    cleaned = cleanup_stale_pid(status) if args.cleanup_stale else False
    if cleaned:
        status = get_bot_status()

    if args.json:
        data = asdict(status)
        data["cleanup_stale_pid"] = cleaned
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(status.message)
        if cleaned:
            print("Stale PID file removed.")
        print(f"Status: {status.status}")
        print(f"PID file: {status.pid_file}")
        print(f"Log: {status.log_file}")
        if status.log_updated_at:
            print(f"Log updated: {status.log_updated_at}")

    return 0 if status.status == "running" else 1


def _read_pid(path: Path) -> int | None:
    try:
        raw = path.read_text(encoding="ascii").strip()
    except FileNotFoundError:
        return None
    if not raw.isdigit():
        return None
    return int(raw)


def _is_process_alive(pid: int | None) -> bool:
    if pid is None:
        return False
    if os.name == "nt":
        return _is_windows_process_alive(pid)
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _is_windows_process_alive(pid: int) -> bool:
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            f"if (Get-Process -Id {pid} -ErrorAction SilentlyContinue) {{ 'alive' }}",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore",
        check=False,
    )
    return result.stdout.strip() == "alive"


def _mtime_iso(path: Path) -> str | None:
    if not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()


def _rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
