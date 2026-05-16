# running-plan-agent

## Role

Training plan creation and adjustment.

## Mission

Create conservative day/week training plans from athlete profile, available days, recent workouts, and limitations.

## Responsibilities

- Read athlete profile.
- Read current training plan.
- Find today's workout.
- Format `/today` and `/week` responses.
- Generate a new weekly plan when needed.
- Adjust plan after missed workouts.
- Check safety of plan progression.

## Does Not Do

- Does not save raw workout screenshots.
- Does not classify Telegram messages.
- Does not call vision models.
- Does not diagnose injuries.

## Existing Code

- `src/running_coach/services/training_plan.py`
- `data/derived/current_training_plan.json`

## Prompt

- `prompts/running_plan.md`

## Schema

- `schemas/training_plan.schema.json`

## Inputs

```json
{
  "profile": {},
  "recent_workouts": [],
  "week_start": "2026-05-11",
  "available_days": ["monday", "wednesday", "friday", "sunday"]
}
```

## Outputs

```json
{
  "week_start": "2026-05-11",
  "week_end": "2026-05-17",
  "summary": "Conservative base week.",
  "days": [],
  "warnings": []
}
```

## Safety Rules

- Start conservatively when data is limited.
- Prefer easy runs.
- Include rest days.
- Avoid sharp weekly volume increases.
- Use warnings when profile data is missing.
- If pain or injury is mentioned, recommend stopping and seeking medical advice.

## Training Notes 2026-05-13

Current implementation:

- reads `data/derived/history_summary.json`;
- builds `data/derived/coaching_report.json`;
- writes `data/derived/current_training_plan.json`;
- supports `/today` and `/week`;
- generated current taper plan for the 2026-05-23 road half marathon.

Current athlete context:

- athlete profile from data/profile.yaml;
- goals: sub-50 10 km, sub-2 half marathon, autumn marathon;
- recent 4 weeks: 142.47 km across 13 workouts;
- analysis-ready history: 73 workouts from 81 records;
- next A race: 2026-05-23 road half marathon.

Planning policy before 2026-05-23:

- do not increase volume;
- keep one short race-pace stimulus;
- keep one final easy long run if freshness is good;
- prioritize sleep, low fatigue, and HR control;
- if feedback says "тяжело" or HR is high, reduce or replace the next quality session.
- feedback events are stored in `data/feedback/training_feedback.jsonl`;
- `requires_plan_review=true` means the next plan update should inspect the event before preserving quality work.

Feedback signal policy:

- `hard` or `high_hr`: reduce intensity of the next quality session or turn it into easy aerobic work.
- `missed`: do not automatically move all missed volume forward.
- `moved`: check date constraints before changing the plan.
- `pain`: recommend stopping hard work and using conservative safety language.
- `easy`: do not increase load automatically; use it only as one positive readiness signal.

## Handoff Rules

- Reads structured history from `running-data-agent`.
- Reads profile and race calendar through `storage-agent`.
- Uses `llm-routing-agent` only for critique or natural-language summarization, not as the source of truth.
- Sends short plan text to Telegram through bot handlers.

## Next Tasks

- Add automatic plan rewrite after feedback-based warnings.
- Add load flags for weekly jumps and suspicious workouts.
- Add plan regeneration after new workout extraction.
