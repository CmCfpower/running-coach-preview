from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from running_coach.config import load_project_config
from running_coach.services.workouts import import_workout_file
from running_coach.storage import ProjectStorage


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
DATE_PATTERNS = (
    re.compile(r"(?P<day>\d{2})_(?P<month>\d{2})_(?P<year>\d{2,4})"),
    re.compile(r"(?P<day>\d{2})\.(?P<month>\d{2})\.(?P<year>\d{2,4})"),
    re.compile(r"(?P<year>20\d{2})-(?P<month>\d{2})-(?P<day>\d{2})"),
    re.compile(r"(?P<year>20\d{2})(?P<month>\d{2})(?P<day>\d{2})"),
)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Batch import workout screenshots from a folder.")
    parser.add_argument(
        "folder",
        nargs="?",
        default=str(ROOT / "data" / "Running"),
        help="Source folder, default: data/Running",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show what would be imported.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Import files even if they are already listed in the import manifest.",
    )
    args = parser.parse_args()

    source_root = Path(args.folder).resolve()
    if not source_root.exists():
        raise FileNotFoundError(f"Source folder does not exist: {source_root}")

    config = load_project_config(ROOT / "project.yaml")
    storage = ProjectStorage(config.root)

    images = sorted(
        path for path in source_root.rglob("*") if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )
    manifest_path = storage.resolve("data/derived/workout_import_manifest.json")
    already_imported = set()
    if manifest_path.exists() and not args.force:
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for item in existing_manifest.get("imported", []):
            if isinstance(item, dict) and "source_file" in item and not item.get("dry_run"):
                already_imported.add(item["source_file"])
        for item in existing_manifest.get("skipped_existing", []):
            if isinstance(item, dict) and "source_file" in item:
                already_imported.add(item["source_file"])

    manifest = {
        "source_root": str(source_root),
        "dry_run": args.dry_run,
        "force": args.force,
        "total_images": len(images),
        "previously_imported": len(already_imported),
        "skipped_existing": [],
        "imported": [],
        "unparsed": [],
        "references": _reference_files(source_root),
    }

    for image in images:
        if str(image) in already_imported:
            manifest["skipped_existing"].append({"source_file": str(image), "reason": "already_imported"})
            continue

        workout_date = _date_from_path(image)
        if workout_date is None:
            manifest["unparsed"].append({"source_file": str(image), "reason": "date_not_detected"})
            continue

        if args.dry_run:
            manifest["imported"].append(
                {
                    "source_file": str(image),
                    "date": workout_date,
                    "dry_run": True,
                }
            )
            continue

        result = import_workout_file(
            storage,
            workout_date,
            image,
            source="history",
            caption=f"Imported from {image.relative_to(source_root)}",
        )
        manifest["imported"].append({"source_file": str(image), **asdict(result)})

    output_name = "workout_import_manifest.dry-run.json" if args.dry_run else "workout_import_manifest.json"
    manifest_path = storage.write_json(f"data/derived/{output_name}", manifest)
    print(f"Images found: {manifest['total_images']}")
    print(f"Skipped existing: {len(manifest['skipped_existing'])}")
    print(f"Imported: {len(manifest['imported'])}")
    print(f"Unparsed: {len(manifest['unparsed'])}")
    print(f"References: {len(manifest['references'])}")
    print(f"Manifest: {storage.relative(manifest_path)}")
    return 0


def _date_from_path(path: Path) -> str | None:
    for part in reversed(path.parts):
        parsed = _date_from_text(part)
        if parsed is not None:
            return parsed
    return None


def _date_from_text(text: str) -> str | None:
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match is None:
            continue

        day = int(match.group("day"))
        month = int(match.group("month"))
        year_text = match.group("year")
        year = int(year_text)
        if year < 100:
            year += 2000

        try:
            parsed = date(year, month, day)
        except ValueError:
            continue
        return parsed.isoformat()
    return None


def _reference_files(source_root: Path) -> list[dict[str, str | int]]:
    result = []
    for path in sorted(source_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() in IMAGE_EXTENSIONS:
            continue
        result.append(
            {
                "path": str(path),
                "relative_path": str(path.relative_to(source_root)),
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
            }
        )
    return result


if __name__ == "__main__":
    raise SystemExit(main())
