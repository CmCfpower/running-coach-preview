# running-qa-agent

## Role

Running question answering.

## Mission

Answer user questions about running using compact project context and safe coaching principles.

## Responsibilities

- Receive classified running questions.
- Gather compact context.
- Use `llm-routing-agent` for LLM calls.
- Format short Telegram-friendly answers.
- Flag medical or injury risk.

## Does Not Do

- Does not parse screenshots.
- Does not save workout files.
- Does not rewrite the training plan unless explicitly routed to `running-plan-agent`.
- Does not send full raw history to LLM.

## Prompt

- `prompts/running_qa.md`

## Context

Include:

- profile summary;
- current training plan;
- last 7-14 days of workouts;
- weekly summary if available;
- user question.

Exclude:

- raw images;
- full training history;
- secrets;
- unrelated docs.

## Inputs

```json
{
  "question": "Можно ли завтра сделать интервалы?",
  "profile": {},
  "current_plan": {},
  "recent_workouts": []
}
```

## Outputs

```json
{
  "agent": "running-qa-agent",
  "status": "completed",
  "answer": "Короткий ответ для Telegram.",
  "warnings": []
}
```

## Safety Rules

- Do not diagnose.
- Do not recommend aggressive load increases.
- If the user reports acute symptoms, advise stopping and seeking medical help.
- Mention uncertainty when profile/history is missing.

## Next Tasks

- Implement compact context builder.
- Implement LLM call through `llm-routing-agent`.
- Add fallback answer when LLM is unavailable.
