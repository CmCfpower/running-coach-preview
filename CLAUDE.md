# CLAUDE.md

You are working on `running-coach`, a local filesystem-first AI running coach project.

## What Matters Most

The user plans to continue development primarily in Claude and Qwen. Keep the project portable:

- no Codex-only assumptions;
- plain Python code;
- clear docs;
- prompts and schemas as files;
- local data in `data/`;
- minimal external infrastructure for MVP.

## Read First

Before making changes, read:

1. `docs/project-goals.md`
2. `docs/technical-spec.md`
3. `docs/agents-architecture.md`
4. `docs/agent-training-plan.md`
5. `docs/skills-training-map.md`
6. `project.yaml`

## Current Phase

Phase 0: portable foundation.

The next practical goal is to prepare:

- `.env.example`;
- `AGENTS.md`;
- `CLAUDE.md`;
- `prompts/`;
- `schemas/`;
- basic `src/running_coach/` package;
- then implement the running Telegram MVP.

## MVP Boundaries

Do not introduce required dependencies on:

- Postgres;
- Redis;
- Qdrant;
- Minio;
- VDS;
- Caddy;
- production auth.

These belong after the first useful bot works.

## Data Safety

Fitness and nutrition data are private. Keep raw data local unless explicitly needed for one-time extraction. Summaries and structured JSON should be used for later reasoning.

## Agent Model

Treat agents as logical responsibilities first, not necessarily separate processes/classes:

- `storage-agent`
- `running-intake-agent`
- `running-data-agent`
- `running-plan-agent`
- `running-qa-agent`
- `llm-routing-agent`
- `documentation-agent`

Use `docs/agents-architecture.md` for boundaries.

## Style

Be conservative and practical. Build the smallest working thing that keeps future migration easy.
