"""Project configuration loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from running_coach.simple_yaml import load_simple_yaml


@dataclass(frozen=True)
class BotConfig:
    env_token: str
    default_agent: str


@dataclass(frozen=True)
class StorageConfig:
    workouts: Path
    nutrition: Path
    reports: Path
    dashboard: Path


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    version: str
    root: Path
    timezone: str
    running_bot: BotConfig
    nutrition_bot: BotConfig
    agents: tuple[str, ...]
    storage: StorageConfig


def load_project_config(path: str | Path = "project.yaml") -> ProjectConfig:
    """Load project.yaml into a typed config object."""

    config_path = Path(path).resolve()
    raw = load_simple_yaml(config_path)
    root = Path(str(raw["root"])).resolve()
    bots = raw.get("bots", {})
    storage = raw.get("storage", {})

    return ProjectConfig(
        name=str(raw["name"]),
        version=str(raw["version"]),
        root=root,
        timezone=str(raw.get("timezone", "Europe/Moscow")),
        running_bot=_bot_config(bots.get("running", {})),
        nutrition_bot=_bot_config(bots.get("nutrition", {})),
        agents=tuple(str(agent) for agent in raw.get("agents", [])),
        storage=StorageConfig(
            workouts=_project_path(root, storage.get("workouts", "data/workouts")),
            nutrition=_project_path(root, storage.get("nutrition", "data/nutrition")),
            reports=_project_path(root, storage.get("reports", "reports")),
            dashboard=_project_path(root, storage.get("dashboard", "dashboard")),
        ),
    )


def _bot_config(raw: dict[str, Any]) -> BotConfig:
    return BotConfig(
        env_token=str(raw.get("env_token", "")),
        default_agent=str(raw.get("default_agent", "")),
    )


def _project_path(root: Path, value: Any) -> Path:
    path = Path(str(value))
    if path.is_absolute():
        return path.resolve()
    return (root / path).resolve()
