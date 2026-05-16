# План обучения агентов Running Coach

Дата: 2026-05-12  
Источник для подбора skills: https://skills.sh/vercel-labs/skills/find-skills

## 1. Подход

Обучение агентов в проекте означает не fine-tuning модели, а назначение каждому агенту:

- зоны ответственности;
- входных и выходных артефактов;
- обязательных навыков;
- рекомендуемых external skills;
- правил, когда агент может действовать сам, а когда обязан передать задачу другому агенту.

## 2. Правила подбора skills

Используем подход из `find-skills`:

1. Определить домен задачи: backend, frontend, testing, docs, deployment, LLM, data.
2. Определить конкретную операцию: написать бота, проверить UI, подготовить Vercel-деплой, создать schema.
3. Искать skill в каталоге skills.sh.
4. Проверять качество:
   - источник;
   - количество установок;
   - репутация репозитория;
   - соответствие задаче.
5. Не устанавливать слабые или нерелевантные skills только потому, что они найдены.
6. Если подходящего skill нет, создать локальную инструкцию в `AGENTS.md`, `CLAUDE.md` или собственный skill позже.

## 3. Базовые skills-кандидаты

| Skill | Источник | Назначение | Кому полезен | Статус |
|---|---|---|---|---|
| `find-skills` | `vercel-labs/skills` | поиск и оценка skills | `documentation-agent`, `project-orchestrator` | recommended |
| `skill-creator` | `anthropics/skills` | создание собственных skills | `documentation-agent`, `platform-domain-agent` | recommended |
| `frontend-design` | `anthropics/skills` | дизайн интерфейсов | `dashboard-agent` | recommended |
| `web-design-guidelines` | `vercel-labs/agent-skills` | web UI guidelines | `dashboard-agent` | recommended |
| `agent-browser` | `vercel-labs/agent-browser` | browser automation и проверка UI | `dashboard-agent`, `testing-agent` | recommended |
| `webapp-testing` | `anthropics/skills` | тестирование web-приложений | `testing-agent`, `dashboard-agent` | recommended |
| `xlsx` | `anthropics/skills` | работа с Excel | `excel-report-agent`, `running-report-agent` | later |
| `deploy-to-vercel` | `vercel-labs/agent-skills` | деплой web-проекта на Vercel | `deployment-agent` | later |
| `vercel-deploy` | `vercel-labs/agent-skills` | быстрый preview deploy | `deployment-agent` | later |
| `systematic-debugging` | `obra/superpowers` | структурная отладка | `platform-domain-agent`, `testing-agent` | candidate |
| `test-driven-development` | `obra/superpowers` | TDD-подход | `testing-agent` | candidate |
| `subagent-driven-development` | `obra/superpowers` | работа через subagents | `project-orchestrator` | candidate |

Примечание: backend/Python/Telegram/LLM skills из каталога нужно отдельно проверять перед установкой. Если надежного готового skill нет, для проекта лучше создать собственные локальные инструкции.

## 4. Матрица обучения агентов

## 4.1 `project-orchestrator`

### Роль

Маршрутизирует задачи между доменами и следит за последовательностью.

### Навыки

- decomposition;
- routing;
- dependency ordering;
- status reporting;
- structured outputs.

### Skills

- `find-skills` - когда нужно подобрать внешний skill;
- `subagent-driven-development` - кандидат для улучшения orchestration;
- локальный `running-coach-orchestration` - создать позже.

### Не делает

- не пишет raw-файлы;
- не вызывает vision напрямую;
- не строит тренировочный план самостоятельно.

## 4.2 `running-domain-agent`

### Роль

Координирует все беговые задачи.

### Навыки

- running domain routing;
- interpretation of training intent;
- Telegram response shaping;
- handoff между intake/data/plan/qa.

### Skills

- локальный `running-domain-basics` - создать позже;
- готового внешнего skill пока не назначаем.

## 4.3 `running-intake-agent`

### Роль

Классифицирует входящие Telegram-сообщения.

### Навыки

- intent classification;
- command parsing;
- caption parsing;
- date hints extraction;
- safe fallback questions.

### Skills

- локальная инструкция в `prompts/running_intake.md`;
- внешний skill не нужен на MVP.

## 4.4 `running-data-agent`

### Роль

Хранит и нормализует данные тренировок.

### Навыки

- safe file operations;
- JSON/YAML IO;
- schema validation;
- workout object normalization;
- id generation.

### Skills

- локальный `running-workout-data` - создать позже;
- `systematic-debugging` - кандидат для сложных ошибок хранения.

### Субагенты

- `workout-file-agent` - файловые операции;
- `workout-parser-agent` - OCR/vision extraction;
- `workout-validation-agent` - проверка схемы и здравого смысла.

## 4.5 `running-plan-agent`

### Роль

Создает и корректирует тренировочные планы.

### Навыки

- conservative training planning;
- weekly load reasoning;
- fatigue/risk checks;
- HR zones;
- plan JSON generation.

### Skills

- локальный `running-plan-basics` - создать позже;
- внешние skills пока не назначаем, потому что нужна доменная осторожность.

### Субагенты

- `profile-analysis-agent`;
- `training-load-agent`;
- `plan-builder-agent`;
- `plan-safety-agent`.

## 4.6 `running-qa-agent`

### Роль

Отвечает на вопросы по бегу.

### Навыки

- compact context gathering;
- safe coaching tone;
- clear Telegram answers;
- uncertainty handling;
- medical caution boundaries.

### Skills

- локальный `running-qa` через `prompts/running_qa.md`;
- внешний skill не нужен на MVP.

## 4.7 `running-report-agent`

### Роль

Готовит недельные отчеты, Excel и данные для dashboard.

### Навыки

- weekly summaries;
- trends;
- compliance analysis;
- Excel generation;
- dashboard JSON.

### Skills

- `xlsx` - для Excel-отчетов после MVP;
- `webapp-testing` - для проверки dashboard после появления UI;
- локальный `running-analytics` - создать позже.

## 4.8 `nutrition-domain-agent`

### Роль

Координирует питание.

### Навыки

- meal flow routing;
- nutrition context;
- training-aware nutrition;
- uncertainty communication.

### Skills

- локальный `nutrition-basics` - создать позже;
- внешний skill пока не назначаем.

## 4.9 `nutrition-data-agent`

### Роль

Сохраняет фото еды и оценивает БЖУ.

### Навыки

- image intake;
- meal JSON;
- nutrition estimate ranges;
- confidence handling;
- portion clarification.

### Skills

- локальный `meal-estimation` - создать позже;
- vision model integration через `llm-routing-agent`.

## 4.10 `grocery-agent`

### Роль

Ведет продукты, остатки и покупки.

### Навыки

- list parsing;
- inventory management;
- threshold reminders;
- weekly menu alignment.

### Skills

- локальный `grocery-inventory` - создать позже.

## 4.11 `storage-agent`

### Роль

Единый безопасный слой файлового хранения.

### Навыки

- path boundary checks;
- atomic writes;
- JSON/YAML read/write;
- schema validation;
- migration preparation.

### Skills

- `systematic-debugging` - кандидат;
- локальный `safe-local-storage` - создать позже.

## 4.12 `llm-routing-agent`

### Роль

Выбирает модель, ограничивает контекст и выполняет вызовы LLM.

### Навыки

- OpenAI-compatible API;
- routing by task type;
- fallback;
- error logging;
- prompt loading;
- token budgeting.

### Skills

- локальный `llm-routing-policy` - создать позже.

## 4.13 `dashboard-agent`

### Роль

Создает и поддерживает web-dashboard.

### Навыки

- UI layout;
- responsive design;
- static dashboard;
- data visualization;
- browser verification;
- future Vercel readiness.

### Skills

- `frontend-design`;
- `web-design-guidelines`;
- `agent-browser`;
- `webapp-testing`;
- `deploy-to-vercel` later.

## 4.14 `documentation-agent`

### Роль

Поддерживает проектную документацию.

### Навыки

- README;
- AGENTS.md;
- CLAUDE.md;
- technical spec;
- changelog;
- skill search and evaluation.

### Skills

- `find-skills`;
- `skill-creator`;
- локальный `running-coach-docs` - создать позже.

## 4.15 `deployment-agent`

### Роль

Готовит Vercel/VDS-деплой после MVP.

### Навыки

- Vercel deployment;
- environment variables;
- static frontend deployment;
- backend/VDS planning;
- health checks;
- backups.

### Skills

- `deploy-to-vercel`;
- `vercel-deploy`;
- возможно `vercel-cli-with-tokens` later.

## 5. Что обучаем первым

На ближайший этап не нужно устанавливать все skills. Сначала достаточно обучить MVP-агентов локальными инструкциями.

### Первая партия

1. `documentation-agent`
   - оформить `AGENTS.md`;
   - оформить `CLAUDE.md`;
   - добавить правила работы с skills.

2. `storage-agent`
   - описать безопасные файловые операции;
   - зафиксировать схемы данных.

3. `running-intake-agent`
   - описать classification rules;
   - подготовить `prompts/running_intake.md`.

4. `running-data-agent`
   - описать сохранение тренировок;
   - подготовить `workout.schema.json`.

5. `running-qa-agent`
   - подготовить `prompts/running_qa.md`;
   - определить compact context.

6. `dashboard-agent`
   - использовать `frontend-design`/`web-design-guidelines` как ориентир;
   - поддерживать проектный dashboard.

## 6. Команды установки skills

Не выполнять автоматически без необходимости. Команды для будущего:

```powershell
npx skills add https://github.com/vercel-labs/skills --skill find-skills
npx skills add vercel-labs/agent-skills
npx skills add anthropics/skills
npx skills add vercel-labs/agent-browser
```

Если Node/npm недоступны в обычном PowerShell, сначала нужно поставить Node.js или запускать skills CLI в окружении, где доступен `npx`.

## 7. Пометка ответственности

Каждый агент в `docs/agents-architecture.md` должен иметь:

- `Роль`;
- `Ответственность`;
- `Не отвечает за`;
- `Входы`;
- `Выходы`;
- `Навыки`;
- `Skills`;
- `Субагенты`, если есть.

Это и есть минимальная карта обучения агента.
