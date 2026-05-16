from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from running_coach.config import load_project_config
from running_coach.storage import ProjectStorage


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    config = load_project_config(ROOT / "project.yaml")
    storage = ProjectStorage(config.root)
    updated = 0
    hashed = 0

    for parsed_path in sorted(storage.resolve("data/workouts").glob("*/parsed.json")):
        relative = storage.relative(parsed_path)
        record = storage.read_json(relative)
        hashes = dict(record.get("raw_file_hashes", {}))
        changed = False

        for raw_file in record.get("raw_files", []):
            if raw_file in hashes:
                continue
            raw_path = storage.resolve(raw_file)
            if not raw_path.exists():
                continue
            hashes[raw_file] = _sha256_file(raw_path)
            hashed += 1
            changed = True

        if changed:
            record["raw_file_hashes"] = hashes
            storage.write_json(relative, record)
            updated += 1

    print(f"Updated records: {updated}")
    print(f"Hashed files: {hashed}")
    return 0


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
