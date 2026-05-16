# AGENTS.md

## Vault Context

Связанные заметки, решения и контекст проекта живут в Obsidian-vault:
- Reference: `<LOCAL_OBSIDIAN_VAULT>\reference\running-coach.md` — обзор проекта, стек, агенты
- Решения: `<LOCAL_OBSIDIAN_VAULT>\brain\Key Decisions.md`
- Паттерны: `<LOCAL_OBSIDIAN_VAULT>\brain\Patterns.md`
- Грабли: `<LOCAL_OBSIDIAN_VAULT>\brain\Gotchas.md`

При вопросах о контексте, прошлых решениях или паттернах — читай оттуда. Долгоживущие знания (решения, паттерны, грабли) фиксируй в vault, а не в коде.

## Project

`running-coach` is a local AI running coach and nutrition assistant. The project starts as a filesystem-first Telegram MVP and may later grow into a multi-agent system with dashboard, reports, scheduling, nutrition, and infrastructure deployment.

## Current Goal

Build a portable MVP that can be continued in Claude, Qwen, Codex, or another coding agent without relying on Codex-specific runtime features.

## Key Documents

- `docs/project-goals.md` - project goals.
- `docs/technical-spec.md` - detailed technical specification.
- `docs/agents-architecture.md` - agent hierarchy and responsibilities.
- `docs/agent-training-plan.md` - skills and training plan for agents.
- `docs/skills-training-map.md` - external skills mapped to project agents.
- `docs/project-management.md` - current stage, next task, blockers, and PM handoffs.
- `docs/implementation-research.md` - original implementation research.
- `docs/qwen-agent-automation-notes.md` - Qwen agent automation principles extracted from local research.

## MVP Scope

Build one running Telegram bot first:

- read `data/profile.yaml`;
- accept workout screenshots;
- save raw files to `data/workouts/<date>/raw`;
- create or update `parsed.json`;
- show `/profile`, `/today`, `/week`;
- answer running questions using compact context and an OpenAI-compatible LLM endpoint.

Do not require Postgres, Redis, Qdrant, Minio, VDS, or Codex for MVP operation.

## Architecture Rules

- Keep domain responsibilities separated.
- Prefer simple Python modules before creating too many classes.
- Use files and structured JSON/YAML as the MVP contract.
- Store prompts in `prompts/`.
- Store JSON schemas in `schemas/`.
- Keep raw health and fitness data local by default.
- Do not send raw images to LLM more than once for extraction.
- Do not invent unknown workout values; use `null`.
- Keep all file writes inside the project root.
- Treat Qwen as an OpenAI-compatible provider behind `llm-routing-agent`; do not hardcode Qwen SDK assumptions into domain agents.
- Do not put LLM API keys into untrusted third-party agent platforms.

## Agent Responsibilities

Use `docs/agents-architecture.md` as the source of truth.

MVP logical agents:

- `project-manager-agent` - track roadmap, current stage, blockers, next task, and agent handoffs.
- `storage-agent` - safe file IO, JSON/YAML, path boundaries.
- `running-intake-agent` - classify Telegram messages and commands.
- `running-data-agent` - save and normalize workouts.
- `running-plan-agent` - read/create current training plan.
- `running-qa-agent` - answer running questions with compact context.
- `llm-routing-agent` - call OpenAI-compatible LLM endpoints.
- `documentation-agent` - keep docs and roadmap current.

Concrete agent instruction cards live in `agents/`:

- `agents/project-manager-agent.md`
- `agents/project-orchestrator.md`
- `agents/storage-agent.md`
- `agents/running-intake-agent.md`
- `agents/running-data-agent.md`
- `agents/running-plan-agent.md`
- `agents/running-qa-agent.md`
- `agents/llm-routing-agent.md`
- `agents/dashboard-agent.md`
- `agents/documentation-agent.md`

Installed external skills live in `.agents/skills/` and are mapped in
`docs/skills-training-map.md`.

## Coding Guidelines

- Use ordinary Python code.
- Keep modules small and explicit.
- Add tests for schema validation, storage, and command formatting when the code appears.
- Avoid hidden global state except configuration loaded at startup.
- Keep Telegram responses short and readable.
- Log errors locally; do not expose stack traces to Telegram users.

## First Implementation Order

1. Create project structure and schemas.
2. Implement config and storage.
3. Implement profile loading.
4. Implement training plan loading.
5. Implement Telegram skeleton.
6. Implement photo saving.
7. Implement `/today`, `/week`, `/profile`.
8. Add LLM QA flow.

## Commands

Project commands are not finalized yet. When they appear, document them in `README.md`.

Current dashboard task page:

```powershell
cd <PROJECT_ROOT>\dashboard\tasks
powershell -ExecutionPolicy Bypass -File .\start.ps1
```
