# running-intake-agent

## Role

Classifies incoming running-bot messages.

## Mission

Turn raw Telegram updates into structured intent objects that downstream agents can process.

## Responsibilities

- Detect commands.
- Detect workout photos.
- Extract captions.
- Extract date hints.
- Detect running questions.
- Detect missed-workout or plan-change messages.
- Detect post-workout feedback.
- Ask for clarification when intent is unclear.

## Does Not Do

- Does not save files.
- Does not parse screenshots.
- Does not build plans.
- Does not answer coaching questions.

## Prompt

- `prompts/running_intake.md`

## Inputs

```json
{
  "message_type": "text|photo|command",
  "text": "перенеси длинную на воскресенье",
  "caption": null,
  "has_photo": false,
  "current_date": "2026-05-13"
}
```

## Outputs

```json
{
  "type": "training_feedback",
  "date": "2026-05-13",
  "raw_text": "Сделал, было тяжело, пульс высокий",
  "signals": ["completed", "hard", "high_hr"],
  "confidence": 0.95,
  "requires_plan_review": true,
  "notes": ["workout completed", "high perceived effort", "high heart-rate signal"]
}
```

## Classification Types

- `command`
- `workout_photo`
- `running_question`
- `plan_change_request`
- `missed_workout`
- `training_feedback`
- `profile_update`
- `unknown`

## Safety Rules

- Do not invent exact dates from vague phrases without current date context.
- Prefer clarification when confidence is low.
- Keep output machine-readable.
- Pain or injury words must set a conservative plan-review flag.

## Training Notes 2026-05-13

The MVP now supports:

- commands: `/profile`, `/today`, `/week`, `/analysis`;
- workout photos;
- date hints in captions:
  - `2026-05-12`;
  - `12.05.26`;
  - `12.05.2026`;
  - `12_05_26`;
- deterministic post-workout feedback parsing in `src/running_coach/services/feedback.py`.

Current feedback signals:

- `completed`: `сделал`, `выполнил`, `пробежал`, `готово`;
- `hard`: `тяжело`, `сложно`, `еле`, `устал`;
- `easy`: `легко`, `комфортно`, `нормально`, `хорошо`;
- `missed`: `пропустил`, `не сделал`, `не побежал`, `не успел`;
- `moved`: `перенёс`, `перенес`, `перенести`, `сдвинул`;
- `high_hr`: `пульс высокий`, `высокий пульс`, `чсс высок`;
- `pain`: `боль`, `болит`, `травма`, `колено`, `ахилл`.

Feedback is stored in `data/feedback/training_feedback.jsonl` and handed off to
`running-plan-agent` through the `requires_plan_review` flag.

## Handoff Rules

- `command` -> Telegram command handler.
- `workout_photo` -> `running-data-agent`.
- `running_question` -> `running-qa-agent`.
- `training_feedback` -> `running-plan-agent`.
- `plan_change_request` or `missed_workout` -> `running-plan-agent`.
- `profile_update` -> `storage-agent` after confirmation.

## Next Tasks

- Add unit samples for common Russian phrases.
- Add plan adaptation after feedback is recorded.
