# Project Management

Date: 2026-05-15

This document is owned by `project-manager-agent`. It is the short operational
view of the project: current stage, usable functionality, next task, blockers,
and handoff order.

## Current Stage

Running Coach is in the filesystem-first Telegram MVP stage.

Already usable:

- Telegram bot starts locally.
- `/profile`, `/today`, and `/week` work.
- Workout screenshots are saved under `data/workouts/<date>/raw`.
- Vision extraction creates or updates `parsed.json`.
- Duplicate screenshots are detected globally by file hash.
- Misdated screenshot imports can be ignored or relocated to the screenshot date.
- `/today` can show planned work and actual workout data.
- Telegram photo import can return a short workout analysis.
- Telegram photo batches now produce one final recognition message instead of one status message per photo.
- Workout extraction reads up to 8 photos and can derive HR from visible split/lap heart rates.
- Coach review can be called through the OpenAI-compatible LLM endpoint.
- Coach review can create a safe draft adjustment in `data/plan_adjustments/`.
- Draft adjustment can be applied with `/apply_adjustment` or rejected with `/reject_adjustment`.
- Dashboard shows roadmap, tasks, agent status, pipeline, live agent log, and bot runtime state.
- Dashboard roadmap progress is backed by `data/derived/project_status.json`.

## Current Priority

Validate the new Telegram flow with a real photo batch, then continue toward daily-use scheduling.

The target behavior:

1. A workout photo is stored under the actual workout date.
2. The bot returns analysis and compares actual workout vs planned day.
3. Coach review creates a draft adjustment only for the actual workout date.
4. `/adjustment` clearly shows whether the draft is still pending or invalidated.
5. User can safely apply, reject, or ignore a proposed adjustment.

Qwen automation research reviewed on 2026-05-16 confirms the current direction:
keep Qwen behind the OpenAI-compatible `llm-routing-agent`, finish the local
Telegram coaching loop first, and defer CrewAI/LangGraph/Qwen-Agent until a
framework removes real complexity.

## Active Agents

| Agent | Status | Role |
|---|---|---|
| `project-manager-agent` | working | Tracks roadmap, next task, status, blockers, and handoffs. |
| `project-orchestrator` | working | Routes implementation tasks between project agents. |
| `storage-agent` | trained | Keeps local file IO safe and structured. |
| `running-intake-agent` | trained | Classifies Telegram commands, photos, and feedback. |
| `running-data-agent` | working | Saves screenshots, detects duplicates, extracts workout data. |
| `running-plan-agent` | working | Reads plan, compares plan vs actual, requests coach review. |
| `llm-routing-agent` | working | Calls OpenAI-compatible text and vision models. |
| `dashboard-agent` | working | Shows roadmap and agent state. |
| `documentation-agent` | trained | Keeps portable docs current for Codex, Claude, and Qwen. |

## Next Implementation Task

Owner: `running-plan-agent`

Task: validate the fixed Telegram photo-batch and adjustment flow on a real interaction.

Acceptance criteria:

- Sending 4-8 workout screenshots creates one final recognition message.
- Final message includes the number of photos read.
- HR is extracted or derived when visible in split/lap data.
- `/adjustment` displays proposed changes clearly.
- `/reject_adjustment` rejects the active draft without changing the plan.

## PM Review 2026-05-15

Findings:

- Bot runtime is healthy: `scripts/check_bot_status.py --json` reports `running`, PID `12260`.
- Dashboard is reachable at `http://127.0.0.1:4173/`.
- Dashboard browser check passed: runtime row shows `Бот: жив · PID 12260`, agent status is loaded, and browser console has no errors.
- Dashboard live data is only partially proactive:
  - bot runtime, agent status, and agent events are fetched from local API every 15 seconds;
  - roadmap progress and checkbox completion are still calculated from in-browser `localStorage` plus `DEFAULT_DONE`;
  - dashboard does not yet infer completed tasks from code, docs, tests, or PM review automatically.
- Current visible progress `42%` is useful as a rough UI marker, but not reliable as a source of truth.
- `data/plan_adjustments/2026-05-15.json` exists as a pending draft created from coach review.

Decision:

Promote dashboard state model to P1: create a file-backed project status source
so roadmap progress is updated by PM handoff files rather than browser-local
checkbox state.

## Completed 2026-05-15

- Telegram photo handler no longer sends a status response for every incoming photo.
- Extraction reads up to 8 photos in one debounced batch.
- `ExtractionResult` records how many images were read.
- Workout extraction prompt now tells the vision model to derive HR from visible split/lap heart rates when average HR is absent.
- Re-extraction of `2026-05-15` recovered `avg_hr=163` and `max_hr=178`.
- `/reject_adjustment` was added.
- `/adjustment` now shows date, risk, workout id, affected days, proposed changes, and apply/reject commands.
- `data/derived/project_status.json` was added as the file-backed roadmap source.
- Dashboard `/api/project-status` was added and verified; dashboard progress now updates from file-backed status.

## PM Review 2026-05-14

Findings:

- Agent docs and dashboard are mostly aligned.
- `/adjustment` and `/apply_adjustment` exist in code and docs.
- `data/plan_adjustments/2026-05-14.json` exists, so the draft adjustment flow has been exercised.
- `logs/bot.pid` points to PID `11876`, but no active Python process was found during review.

Decision:

Runtime stability was promoted to P0 and implemented before continuing coaching
automation.

## Completed 2026-05-14

- `scripts/check_bot_status.py` reports `running`, `stale_pid`, or `down`.
- `scripts/start_running_bot_background.py` removes stale PID files and refuses
  to start a second bot when one is already running.
- Dashboard API `/api/bot-status` reports runtime state from `logs/bot.pid`.
- Dashboard live row shows bot status and PID.
- Auto coach review after photo extraction was added with duplicate protection.
- Misdated 2026-05-14 workout was marked ignored; invalid 2026-05-14 review/draft was invalidated.
- JSON reading now accepts UTF-8 BOM from Windows tools.

## Completed

- `/adjustment` — shows the latest saved draft adjustment with full context.
- `/apply_adjustment` — applies proposed changes to the next 1-3 days, marks draft as applied.
- Both commands are registered and described in `/start`.

## Blockers

- No hard blocker right now.
- External PM/roadmap skills found through `find-skills` have low install counts,
  so they are not installed by default.
- Qwen model names, pricing, and limits from third-party research must be
  verified against official provider docs before production configuration.
- Production deployment is intentionally deferred until the local MVP is useful.

## Deferred

- Nutrition bot.
- Excel reports.
- Vercel deployment.
- VDS deployment for the bot.
- Postgres/Redis/Qdrant/Minio migration.

## PM Agent Training Notes

`project-manager-agent` uses:

- `find-skills` to discover possible skills before adding new workflows.
- `systematic-debugging` for blocked tasks.
- `skill-creator` later, if the PM workflow should become a reusable local skill.

Discovery results on 2026-05-13:

- `404kidwiz/claude-supercode-skills@project-manager` - 988 installs.
- `jezweb/claude-skills@project-session-management` - 383 installs.
- `aaaaqwq/claude-code-skills@project-management` - 377 installs.
- `jezweb/claude-skills@roadmap` - 521 installs.

Decision: do not install these automatically yet. Use local project instructions
until a candidate has stronger trust signals or a very specific need.
