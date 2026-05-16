"""Safe filesystem storage for the MVP."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from running_coach.simple_yaml import load_simple_yaml


@dataclass(frozen=True)
class WorkoutPaths:
    date: str
    directory: Path
    raw_directory: Path
    parsed_json: Path
    notes_md: Path


class ProjectStorage:
    """Filesystem storage scoped to a single project root."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()

    def resolve(self, *parts: str | Path) -> Path:
        path = self.root.joinpath(*map(Path, parts)).resolve()
        if not _is_relative_to(path, self.root):
            raise ValueError(f"Path escapes project root: {path}")
        return path

    def relative(self, path: str | Path) -> str:
        resolved = Path(path).resolve()
        if not _is_relative_to(resolved, self.root):
            raise ValueError(f"Path escapes project root: {resolved}")
        return resolved.relative_to(self.root).as_posix()

    def ensure_dir(self, *parts: str | Path) -> Path:
        path = self.resolve(*parts)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def read_json(self, *parts: str | Path) -> Any:
        path = self.resolve(*parts)
        return json.loads(path.read_text(encoding="utf-8-sig"))

    def write_json(self, relative_path: str | Path, data: Any) -> Path:
        path = self.resolve(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temp_path.replace(path)
        return path

    def read_yaml(self, *parts: str | Path) -> dict[str, Any]:
        return load_simple_yaml(self.resolve(*parts))

    def workout_paths(self, date: str) -> WorkoutPaths:
        directory = self.ensure_dir("data", "workouts", date)
        raw_directory = self.ensure_dir("data", "workouts", date, "raw")
        return WorkoutPaths(
            date=date,
            directory=directory,
            raw_directory=raw_directory,
            parsed_json=directory / "parsed.json",
            notes_md=directory / "notes.md",
        )

    def next_raw_workout_path(self, date: str, source: str, extension: str) -> Path:
        paths = self.workout_paths(date)
        safe_source = _safe_slug(source)
        safe_extension = extension.lower().lstrip(".") or "bin"

        counter = 1
        while True:
            candidate = paths.raw_directory / f"{safe_source}_{counter:03d}.{safe_extension}"
            if not candidate.exists():
                return candidate
            counter += 1

    def copy_file_into_project(self, source_path: str | Path, destination: str | Path) -> Path:
        source = Path(source_path).resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Source file does not exist: {source}")

        target = self.resolve(destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            raise FileExistsError(f"Destination already exists: {target}")

        shutil.copy2(source, target)
        return target


def _safe_slug(value: str) -> str:
    cleaned = "".join(char if char.isalnum() else "_" for char in value.lower())
    cleaned = "_".join(part for part in cleaned.split("_") if part)
    return cleaned or "file"


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False
