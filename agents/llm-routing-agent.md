# llm-routing-agent

## Role

LLM provider and model routing.

## Mission

Call OpenAI-compatible LLM endpoints with minimal context, correct prompts, error handling, and task-based routing.

## Responsibilities

- Read LLM configuration from environment.
- Load prompts from `prompts/`.
- Select model by task type.
- Send OpenAI-compatible chat/completions requests.
- Handle errors and fallbacks.
- Log failures locally.
- Keep token context compact.

## Does Not Do

- Does not decide training logic.
- Does not save raw files.
- Does not own Telegram UX.
- Does not choose to send raw images unless asked by a domain agent.

## Environment

```env
LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
LLM_VISION_MODEL=
```

Qwen/DashScope can be used through an OpenAI-compatible base URL, for example:

```env
LLM_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
```

Model names are configuration, not code. Do not hardcode Qwen model names in domain agents.

## Routing Policy

- Qwen/default: routine Telegram answers, cleanup, summaries.
- DeepSeek: complex reasoning, plan critique, anomaly analysis.
- Claude: manual review or high-value reasoning only.
- Vision model: workout screenshots and meal photos.

## Inputs

```json
{
  "task_type": "running_qa",
  "prompt": "prompts/running_qa.md",
  "context": {},
  "user_message": "..."
}
```

## Outputs

```json
{
  "agent": "llm-routing-agent",
  "status": "completed",
  "model": "qwen",
  "content": "...",
  "usage": null,
  "warnings": []
}
```

## Safety Rules

- Do not include `.env` contents in prompts.
- Do not send provider API keys to untrusted agent wrappers or third-party platforms.
- Do not send raw image data unless task requires extraction.
- Do not resend raw images after structured extraction exists.
- Keep context limited to the task.
- Return a safe fallback if provider is unavailable.

## Training Notes 2026-05-13

Current implementation:

- `src/running_coach/llm.py`;
- OpenAI-compatible `/chat/completions`;
- `build_client_from_env(vision=True)`;
- text model from `LLM_MODEL`;
- vision model from `LLM_VISION_MODEL`;
- current vision setup: DashScope/Qwen compatible endpoint with `qwen3-vl-plus`.

Operational rules:

- never print API keys or proxy values;
- raw images are allowed only for workout extraction;
- Telegram bot catches LLM errors and logs details locally;
- user-facing errors mention the error class, not secrets or stack traces.

## Handoff Rules

- Receives prompts and content from domain agents.
- Returns text or JSON-like content to the caller.
- Does not decide whether a workout is safe or how a plan changes.
- Does not own persistence.

## Next Tasks

- Add retry/backoff for transient provider failures.
- Add model-specific timeout policy.
- Add usage/cost metadata if provider returns it.
- Add provider profile examples for Qwen, Claude, and local OpenAI-compatible runtimes without exposing real keys.
