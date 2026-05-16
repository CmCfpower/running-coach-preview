from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE = ROOT / ".tools" / "node-v24.15.0-win-x64" / "node.exe"
SERVER = ROOT / "dashboard" / "tasks" / "server.mjs"


def main() -> int:
    if not NODE.exists():
        raise RuntimeError(f"Local Node was not found: {NODE}")

    logs = ROOT / "logs"
    logs.mkdir(exist_ok=True)

    env = os.environ.copy()
    env["PORT"] = env.get("PORT", "4173")
    env["HOST"] = env.get("HOST", "127.0.0.1")

    stdout = (logs / "dashboard_stdout.log").open("ab")
    stderr = (logs / "dashboard_stderr.log").open("ab")
    creationflags = 0
    if os.name == "nt":
        creationflags = (
            subprocess.CREATE_NO_WINDOW
            | subprocess.DETACHED_PROCESS
            | subprocess.CREATE_NEW_PROCESS_GROUP
        )

    process = subprocess.Popen(
        [str(NODE), str(SERVER)],
        cwd=ROOT / "dashboard" / "tasks",
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
        creationflags=creationflags,
    )
    (logs / "dashboard_server.pid").write_text(str(process.pid), encoding="ascii")
    print(f"Dashboard started. PID={process.pid}")
    print(f"URL=http://{env['HOST']}:{env['PORT']}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
