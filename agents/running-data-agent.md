# running-data-agent

## Role

Workout data ingestion and normalization.

## Mission

Save incoming workout files, create structured workout records, and keep raw data linked to parsed data.

## Responsibilities

- Receive classified workout photo tasks.
- Ask `storage-agent` for a safe raw path.
- Save raw workout screenshot.
- Create or update `data/workouts/<date>/parsed.json`.
- Keep `raw_files` as relative paths.
- Preserve user notes.
- Trigger OCR/vision extraction after MVP.
- Validate workout record shape.

## Does Not Do

- Does not create training plans.
- Does not answer running questions.
- Does not estimate nutrition.
- Does not send raw images repeatedly to LLM.

## Related Files

- `schemas/workout.schema.json`
- `prompts/workout_extract.md`
- `src/running_coach/storage.py`

## Inputs

```json
{
  "type": "workout_photo",
  "date": "2026-05-12",
  "source": "telegram",
  "file_name": "photo.jpg",
  "caption": "Легкая 5 км"
}
```

## Outputs

```json
{
  "agent": "running-data-agent",
  "status": "completed",
  "workout_id": "2026-05-12-run-001",
  "raw_files": ["data/workouts/2026-05-12/raw/telegram_001.jpg"],
  "parsed_path": "data/workouts/2026-05-12/parsed.json",
  "warnings": []
}
```

## Parsed Workout Rules

- Unknown values must be `null`.
- `extraction_confidence` is required.
- Do not overwrite raw files.
- If OCR/vision is not available, create a draft record with confidence `0`.

## Training Notes 2026-05-13

Current implementation:

- saves raw files to `data/workouts/<date>/raw`;
- keeps relative paths in `raw_files`;
- stores SHA-256 hashes in `raw_file_hashes`;
- rejects duplicate raw files by hash;
- batches Telegram photos with a short debounce before vision extraction;
- uses `prefer_recent=True` for Telegram photos so fresh `telegram_*` files are extracted before old `history_*` files;
- writes values into one `parsed.json` per date.

Confidence policy:

- `1.0`: all key fields are directly extracted;
- `0.85`: key fields are usable, but distance may be derived from duration and pace;
- `0.45`: partial extraction, manual review needed;
- `0.0-0.2`: not useful for analytics.

## Handoff Rules

- Ask `storage-agent` for safe paths and JSON writes.
- Ask `llm-routing-agent` for vision extraction.
- Hand complete `parsed.json` to `running-plan-agent` and history analytics.

## Next Tasks

- Add schema validation tests.
- Add policy for multiple different workouts on the same date.
- Add manual correction command or edit flow.
