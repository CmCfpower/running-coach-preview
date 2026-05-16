# Skills Training Map

Date: 2026-05-13

Source for skill discovery: https://www.skills.sh/vercel-labs/skills/find-skills

This file maps external agent skills to Running Coach logical agents. The
purpose is operational training: each agent gets a small set of skills it should
know how to use or imitate. This is not model fine-tuning.

## Discovery Notes

`find-skills` is the meta-skill for discovering and evaluating skills. It uses
the Skills CLI and recommends candidates based on domain fit, source reputation,
install count, and repository signals.

## Recommended Skill Assignments

| Running Coach Agent | Skills | Why |
|---|---|---|
| `project-manager-agent` | `find-skills`, `systematic-debugging`, `skill-creator` | Track roadmap, choose the next concrete task, evaluate new skills before installation, and create a local PM skill later if needed. |
| `project-orchestrator` | `find-skills`, `systematic-debugging` | Select skills for new project phases and force root-cause thinking when the pipeline breaks. |
| `documentation-agent` | `find-skills`, `skill-creator` | Keep agent docs current and later create local Running Coach skills. |
| `dashboard-agent` | `web-design-guidelines`, `webapp-testing`, `agent-browser` | Review dashboard UI, test local pages, and verify interactions. |
| `storage-agent` | `systematic-debugging` | Debug path, JSON, duplicate, and migration issues from evidence. |
| `llm-routing-agent` | `systematic-debugging` | Debug provider failures, timeouts, model-routing mistakes, and bad responses. |
| `running-intake-agent` | local instructions first | External skill not needed yet; train with project examples and intent fixtures. |
| `running-data-agent` | `systematic-debugging` | Debug extraction, duplicate detection, schema mismatches, and raw/parsed consistency. |
| `running-plan-agent` | local instructions first | Needs domain-specific conservative coaching rules more than generic skills. |
| `running-qa-agent` | local instructions first | Needs compact context and safety boundaries from this project. |
| `running-report-agent` | `xlsx`, `webapp-testing` | Generate Excel reports later and verify report dashboard views. |
| `nutrition-data-agent` | local instructions first, then vision workflow reuse | Meal estimation should reuse the existing LLM/vision policy before adding more skills. |
| `deployment-agent` | `vercel-deploy`, `deploy-to-vercel` | Later Vercel preview/deployment of the static dashboard. |

## Skill Candidates

### `find-skills`

- Source: `vercel-labs/skills`
- Install:

```powershell
npx skills add https://github.com/vercel-labs/skills --skill find-skills
```

- Use for: discovering and evaluating new skills before installing them.
- Assigned to: `project-orchestrator`, `documentation-agent`.

### `skill-creator`

- Source: `anthropics/skills`
- Install:

```powershell
npx skills add https://github.com/anthropics/skills --skill skill-creator
```

- Use for: creating local Running Coach skills with tests and iterative review.
- Assigned to: `documentation-agent`.

### `web-design-guidelines`

- Source: `vercel-labs/agent-skills`
- Install:

```powershell
npx skills add https://github.com/vercel-labs/agent-skills --skill web-design-guidelines
```

- Use for: auditing dashboard UI and accessibility.
- Assigned to: `dashboard-agent`.

### `webapp-testing`

- Source: `anthropics/skills`
- Install:

```powershell
npx skills add https://github.com/anthropics/skills --skill webapp-testing
```

- Use for: testing local web dashboards with Playwright scripts and server lifecycle helpers.
- Assigned to: `dashboard-agent`, `running-report-agent`.

### `agent-browser`

- Source: `vercel-labs/agent-browser`
- Install:

```powershell
npx skills add https://github.com/vercel-labs/agent-browser --skill agent-browser
```

- Use for: persistent browser automation when dashboard testing needs real browser sessions.
- Assigned to: `dashboard-agent`, `testing-agent` later.

### `systematic-debugging`

- Source: `obra/superpowers`
- Install:

```powershell
npx skills add https://github.com/obra/superpowers --skill systematic-debugging
```

- Use for: root-cause debugging across bot, storage, LLM, and extraction flows.
- Assigned to: `project-orchestrator`, `storage-agent`, `running-data-agent`, `llm-routing-agent`.

### `xlsx`

- Source: `anthropics/skills`
- Install:

```powershell
npx skills add https://github.com/anthropics/skills --skill xlsx
```

- Use for: later Excel reports with formatting and formulas.
- Assigned to: `running-report-agent`.

### `vercel-deploy`

- Source: `vercel-labs/agent-skills`
- Install:

```powershell
npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-deploy
```

- Use for: later preview deployment of the static dashboard.
- Assigned to: `deployment-agent`.

## Installation Policy

Do not install every candidate now. Install only when a near-term task needs it:

1. Dashboard polishing/testing: `web-design-guidelines`, `webapp-testing`.
2. Debugging recurring failures: `systematic-debugging`.
3. Local skill creation for Claude/Qwen portability: `skill-creator`.
4. Excel reports: `xlsx`.
5. Deployment: `vercel-deploy`.

## Current Status

| Skill | Status | Reason |
|---|---|---|
| `find-skills` | installed | Installed to `.agents/skills/find-skills`; used for future skill discovery. |
| `web-design-guidelines` | installed | Installed to `.agents/skills/web-design-guidelines`; assigned to `dashboard-agent`. |
| `webapp-testing` | installed | Installed to `.agents/skills/webapp-testing`; assigned to `dashboard-agent`. |
| `systematic-debugging` | installed | Installed to `.agents/skills/systematic-debugging`; assigned to runtime/debug agents. |
| `skill-creator` | installed | Installed to `.agents/skills/skill-creator`; assigned to `documentation-agent`. |
| `xlsx` | later | Wait until Excel reports are started. |
| `vercel-deploy` | later | Wait until Vercel deployment is requested. |

## Project Manager Discovery

On 2026-05-13, `find-skills` was used for:

```powershell
npx.cmd skills find "project management"
npx.cmd skills find "roadmap task management"
```

Best visible candidates:

| Candidate | Installs | Decision |
|---|---:|---|
| `404kidwiz/claude-supercode-skills@project-manager` | 988 | Candidate only; below the preferred 1K+ threshold. |
| `jezweb/claude-skills@project-session-management` | 383 | Candidate only. |
| `aaaaqwq/claude-code-skills@project-management` | 377 | Candidate only. |
| `jezweb/claude-skills@roadmap` | 521 | Candidate only. |

Decision: do not install a third-party PM skill yet. `project-manager-agent`
uses local instructions plus installed `find-skills`, `systematic-debugging`,
and `skill-creator`.

## Local Node Setup

Portable Node.js is installed under `.tools/node-v24.15.0-win-x64`. The `.tools`
directory is ignored by git and is only a local runtime helper.

Enable Node/npm/npx in a PowerShell session:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-node-path.ps1
```

Use `npm.cmd` and `npx.cmd` in PowerShell to avoid the Windows script execution
policy blocking `.ps1` shims.
