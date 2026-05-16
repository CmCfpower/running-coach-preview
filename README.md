# Running Coach Preview

Public-safe preview of a local filesystem-first Telegram running coach MVP.

This repository intentionally excludes personal data, runtime logs, reports, local secrets, and private training history.


Local-first AI running coach and nutrition assistant.

## MVP Commands

Run the Telegram bot:

```powershell
python scripts\run_running_bot.py
```

Useful running bot commands:

```text
/profile
/today
/week
/analysis
```

When a workout photo is sent to the bot, the file is saved to
`data/workouts/<date>/raw` and then extracted into `parsed.json` with the
configured vision model.

Duplicate raw files are detected by SHA-256 hash and are not saved twice.

Agent documentation:

```text
docs/agents-architecture.md
docs/agent-training-plan.md
docs/agent-training-status.md
docs/skills-training-map.md
agents/*.md
```

Photo captions may include a workout date:

```text
2026-05-12
12.05.26
12.05.2026
12_05_26
```

Start the task dashboard:

```powershell
cd <PROJECT_ROOT>\dashboard\tasks
powershell -ExecutionPolicy Bypass -File .\start.ps1
```

The dashboard reads live local project data from:

```text
data/derived/agent_status.json
data/derived/agent_events.jsonl
data/feedback/training_feedback.jsonl
```

Enable local Node/npm/npx for skills work:

```powershell
cd <PROJECT_ROOT>
powershell -ExecutionPolicy Bypass -File .\scripts\setup-node-path.ps1
npx.cmd --version
```

Install a skill candidate after Node is enabled:

```powershell
npx.cmd skills add https://github.com/vercel-labs/skills --skill find-skills
```

Import historical workout screenshots:

```powershell
python scripts\import_workout_folder.py data\Running
```

Preview workout extraction candidates:

```powershell
python scripts\extract_workouts.py --dry-run --limit 5
```

Extract structured workout values with a configured vision model:

```powershell
python scripts\extract_workouts.py --limit 3
```

Required `.env` values for extraction:

```text
LLM_BASE_URL=
LLM_API_KEY=
LLM_VISION_MODEL=
```

Current local setup uses DashScope/Qwen:

```text
LLM_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
LLM_VISION_MODEL=qwen3-vl-plus
```
