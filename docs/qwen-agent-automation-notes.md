# Qwen Agent Automation Notes

Date: 2026-05-16

Source: `Автоматизация тренировок для target race_ Интеграция Qwen 3.5 Plus с агентскими фреймворками — от теории к практике.md`

This note extracts the project-relevant principles from the Qwen automation research. External claims from the source document should be verified against official provider documentation before production use.

## Practical Takeaways

- Qwen should be treated as an OpenAI-compatible LLM provider behind `llm-routing-agent`, not as a hard dependency spread through domain code.
- The MVP should keep agent behavior as explicit Python workflows, prompts, JSON contracts, and files. A full multi-agent framework is a later migration, not a prerequisite.
- The most valuable loop is: workout data -> structured extraction -> plan-vs-actual comparison -> coach analysis -> safe draft adjustment -> Telegram summary.
- Long context is useful, but the system should still pass compact summaries instead of dumping raw history into every request.
- Raw screenshots should be sent only for the first extraction pass. Later agents work with `parsed.json`, summaries, and plan files.
- API keys must stay in local environment/config files and should never be entered into untrusted third-party agent platforms.

## Platform Strategy

### Now

Use the existing local Python bot and `llm-routing-agent`.

Recommended provider shape:

```env
LLM_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
LLM_API_KEY=...
LLM_MODEL=...
LLM_VISION_MODEL=...
```

Model names and pricing are intentionally not hardcoded in project rules because they can change.

### Later

After the Telegram MVP is stable, consider one of these layers:

- Open WebUI for manual experiments with plans, history, and prompts.
- LangGraph or CrewAI if we need explicit multi-step agent orchestration.
- Qwen-Agent if Qwen-native tool use, RAG, or MCP becomes materially useful.

Do not add a framework until it removes real complexity from the current code.

## Security Rules

- Use only official or self-hosted endpoints for API keys.
- Do not place DashScope, Claude, OpenAI, or other provider keys into unknown wrappers.
- Keep `.env`, key files, proxy data, and tokens out of prompts, logs, dashboard payloads, and Telegram replies.
- When using external skills or agent frameworks, treat them as code dependencies: inspect source, pin versions when possible, and avoid granting broad filesystem/network access by default.

## Running Coach Agent Mapping

| Need from source research | Current project owner |
|---|---|
| Qwen provider config | `llm-routing-agent` |
| Workout data collection | `running-data-agent` |
| Plan-vs-actual comparison | `running-plan-agent` |
| Recovery/risk analysis | `running-plan-agent`, later `training-load-agent` |
| Telegram delivery | `running-intake-agent` + bot runtime |
| Progress and roadmap control | `project-manager-agent` |
| Dashboard visibility | `dashboard-agent` |

## Implementation Implication

The next useful development step is not adding CrewAI/LangChain immediately. It is to finish the local end-to-end coaching loop:

1. accept a real workout batch in Telegram;
2. extract accurate date, distance, pace, duration, HR, and notes;
3. compare with the plan for the actual workout date;
4. ask the coach model for analysis;
5. save a safe draft adjustment;
6. return a short Telegram summary with apply/reject commands.

