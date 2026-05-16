# storage-agent

## Role

Safe local filesystem storage layer.

## Mission

Provide reliable file operations inside the project root for JSON, YAML, raw workout files, derived summaries, and future migration.

## Responsibilities

- Resolve paths safely inside project root.
- Reject path traversal outside project root.
- Read JSON.
- Write JSON atomically.
- Read simple YAML files.
- Create required directories.
- Generate workout date directories.
- Generate unique raw file names.
- Return relative paths for data files.

## Does Not Do

- Does not interpret workout meaning.
- Does not call OCR/vision.
- Does not build training plans.
- Does not answer Telegram messages.

## Existing Code

- `src/running_coach/storage.py`
- `src/running_coach/config.py`
- `src/running_coach/simple_yaml.py`

## Inputs

```json
{
  "operation": "write_json|read_json|read_yaml|next_raw_workout_path",
  "path": "data/derived/current_training_plan.json",
  "data": {}
}
```

## Outputs

```json
{
  "agent": "storage-agent",
  "status": "completed",
  "artifact": "data/workouts/2026-05-12/raw/telegram_001.jpg",
  "relative_path": "data/workouts/2026-05-12/raw/telegram_001.jpg"
}
```

## Safety Rules

- Never write outside `PROJECT_ROOT`.
- Never overwrite raw files.
- Use `null` for unknown structured values.
- Store paths in JSON as relative POSIX-style paths.
- Keep secrets out of JSON/YAML data files.

## Training Notes 2026-05-13

Current implementation:

- `ProjectStorage.resolve()` rejects paths outside the project root;
- `write_json()` writes atomically through a temporary file;
- `next_raw_workout_path()` creates unique raw names;
- workout dates live under `data/workouts/<date>`;
- `raw_file_hashes` are now stored in workout records for duplicate detection.

Storage contracts:

- secrets stay in `.env` and `Keys.txt`, never in derived JSON;
- raw file paths in JSON use relative POSIX-style strings;
- derived analytics live under `data/derived`;
- reports live under `reports`.

## Handoff Rules

- Domain agents ask for safe paths and JSON IO.
- Storage does not interpret workout meaning.
- Storage does not call LLM or Telegram.

## Next Tasks

- Add tests for path boundary checks.
- Add helper for appending JSONL events.
- Add backup/export helper before larger migrations.
