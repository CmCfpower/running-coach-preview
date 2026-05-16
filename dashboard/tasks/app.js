const STORAGE_KEY = "runningCoachRoadmapProgress";
const THEME_KEY = "runningCoachRoadmapTheme";
const RUNTIME_REFRESH_MS = 15000;

const DEFAULT_DONE = {
  "foundation:dirs": true,
  "foundation:schemas": true,
  "foundation:env": true,
  "foundation:agents-doc": true,
  "running-bot-mvp:bot-skeleton": true,
  "running-bot-mvp:photo-save": true,
  "running-bot-mvp:manual-date": true,
  "running-bot-mvp:profile-command": true,
  "plan-basic:plan-json": true,
  "plan-basic:today": true,
  "plan-basic:week": true,
  "plan-basic:adjust-text": true,
  "llm-context:llm-client": true,
  "llm-context:prompts": true,
  "extractor:batch-import": true,
  "extractor:parsed-json": true,
  "extractor:vision-once": true,
  "extractor:weekly-summary": true,
};

const stages = [
  {
    id: "foundation",
    number: "Этап 0",
    title: "Переносимый фундамент",
    status: "active",
    duration: "12 мая - 13 мая",
    usable: "Готовит проект к разработке в Claude и Qwen",
    description:
      "Фиксируем структуру проекта, схемы, промпты и документацию так, чтобы Codex не был обязательной частью дальнейшей разработки.",
    tasks: [
      ["dirs", "Создать рабочую структуру data, reports, dashboard", "core"],
      ["schemas", "Описать JSON-схемы тренировок, питания и плана", "data"],
      ["env", "Добавить .env.example и настройки LLM/Telegram", "ops"],
      ["agents-doc", "Добавить AGENTS.md/CLAUDE.md для будущих ИИ-агентов", "docs"],
    ],
  },
  {
    id: "running-bot-mvp",
    number: "Этап 1",
    title: "Беговой бот на файловой системе",
    status: "planned",
    duration: "13 мая - 15 мая",
    usable: "Первые реальные загрузки тренировок",
    description:
      "Минимальный Telegram-бот принимает фото тренировок, сохраняет их по датам и отвечает базовыми командами без Postgres и Redis.",
    tasks: [
      ["bot-skeleton", "Собрать Python Telegram bot skeleton", "bot"],
      ["photo-save", "Сохранять фото в data/workouts/<date>/raw", "files"],
      ["manual-date", "Добавить ручное указание даты тренировки", "ux"],
      ["profile-command", "Сделать /profile и чтение data/profile.yaml", "bot"],
    ],
  },
  {
    id: "plan-basic",
    number: "Этап 2",
    title: "План дня и недели",
    status: "planned",
    duration: "15 мая - 17 мая",
    usable: "Ботом уже можно пользоваться как тренером",
    description:
      "Появляется план тренировок в JSON/Markdown и команды, которые показывают назначение на сегодня и неделю.",
    tasks: [
      ["plan-json", "Создать формат недельного плана", "data"],
      ["today", "Добавить команду /today", "bot"],
      ["week", "Добавить команду /week", "bot"],
      ["adjust-text", "Обработать сообщения о пропуске или переносе тренировки", "agent"],
    ],
  },
  {
    id: "llm-context",
    number: "Этап 3",
    title: "QA через Claude/Qwen",
    status: "planned",
    duration: "17 мая - 19 мая",
    usable: "Можно задавать вопросы по бегу",
    description:
      "Подключаем LLM через OpenAI-compatible API, выносим промпты в файлы и ограничиваем контекст профилем, планом и последними тренировками.",
    tasks: [
      ["llm-client", "Сделать единый LLM client с base_url/model/api_key", "llm"],
      ["prompts", "Вынести промпты в prompts/*.md", "prompt"],
      ["context-pack", "Собирать компактный контекст для running QA", "tokens"],
      ["qa-route", "Отправлять обычные текстовые вопросы в QA-flow", "bot"],
    ],
  },
  {
    id: "schedule",
    number: "Этап 4",
    title: "Напоминания и стабильный режим",
    status: "planned",
    duration: "19 мая - 21 мая",
    usable: "Ежедневное использование без ручного запуска сценариев",
    description:
      "Добавляем утренние сообщения, воскресный обзор и контроль пропущенных тренировок в простой файловой конфигурации.",
    tasks: [
      ["schedule-config", "Создать data/schedule.yaml", "config"],
      ["morning", "Добавить утреннее сообщение с планом дня", "bot"],
      ["weekly", "Добавить воскресную сводку", "analytics"],
      ["missed", "Спрашивать статус при пропущенной тренировке", "coach"],
    ],
  },
  {
    id: "extractor",
    number: "Этап 5",
    title: "Импорт и распознавание тренировок",
    status: "planned",
    duration: "21 мая - 25 мая",
    usable: "История тренировок начинает работать на план",
    description:
      "Исторические скриншоты и новые фото превращаются в структурированные parsed.json с кэшированием результата.",
    tasks: [
      ["batch-import", "Сделать batch import исторических скриншотов", "import"],
      ["vision-once", "Запускать vision/OCR один раз на файл", "tokens"],
      ["parsed-json", "Создавать parsed.json рядом с raw", "data"],
      ["weekly-summary", "Генерировать недельные summary", "analytics"],
    ],
  },
  {
    id: "reports-dashboard",
    number: "Этап 6",
    title: "Отчеты и dashboard",
    status: "planned",
    duration: "25 мая - 31 мая",
    usable: "Появляется визуальный контроль прогресса",
    description:
      "Добавляем Excel-отчет и первую версию dashboard с тренировками, трендами, планом и текущей неделей.",
    tasks: [
      ["excel", "Генерировать reports/training_plan.xlsx", "report"],
      ["dashboard-app", "Собрать dashboard MVP", "web"],
      ["charts", "Показать недельную дистанцию, темп и пульс", "charts"],
      ["calendar", "Добавить календарь плана", "plan"],
    ],
  },
  {
    id: "nutrition",
    number: "Этап 7",
    title: "Нутрициолог MVP",
    status: "planned",
    duration: "1 июня - 7 июня",
    usable: "Можно вести питание рядом с тренировками",
    description:
      "Второй бот или режим питания принимает фото еды, оценивает диапазоны калорий/БЖУ и ведет простой список продуктов.",
    tasks: [
      ["meal-photo", "Сохранять фото еды по датам и приемам пищи", "food"],
      ["meal-estimate", "Оценивать калории и БЖУ диапазонами", "llm"],
      ["daily-food", "Давать рекомендации на остаток дня", "coach"],
      ["groceries", "Вести inventory.json и список покупок", "grocery"],
    ],
  },
  {
    id: "infra-migration",
    number: "Этап 8",
    title: "Инфраструктура и деплой",
    status: "planned",
    duration: "после стабильного MVP",
    usable: "Готовность к Vercel/VDS и большим данным",
    description:
      "Только после полезного MVP переносим данные и сервисы в более тяжелую инфраструктуру: Postgres, Redis, Qdrant, Minio, Vercel/VDS.",
    tasks: [
      ["postgres", "Мигрировать ключевые JSON в Postgres", "db"],
      ["redis", "Вынести очереди и расписания в Redis/worker", "ops"],
      ["qdrant", "Добавить семантическую память через Qdrant", "memory"],
      ["deploy", "Подготовить Vercel/VDS deployment checklist", "deploy"],
    ],
  },
];

let agents = [
  {
    id: "project-manager-agent",
    domain: "platform",
    name: "project-manager-agent",
    status: "working",
    priority: "P0",
    task: "Roadmap, current stage, blockers, next task, agent handoffs",
    input: "docs, dashboard status, user priorities, agent event log",
    output: "next task brief, acceptance criteria, updated project status",
    training: "Trained with find-skills; uses local PM rules instead of low-trust third-party PM skills",
    skills: "find-skills, systematic-debugging, skill-creator",
    artifact: "docs/project-management.md",
  },
  {
    id: "project-orchestrator",
    domain: "platform",
    name: "project-orchestrator",
    status: "done",
    priority: "P1",
    task: "Цели, ТЗ, архитектура агентов, training plan",
    input: "Исследование, решения пользователя",
    output: "Документы проекта и порядок работ",
    training: "Обучен на docs/* и AGENTS.md",
    skills: "find-skills, systematic-debugging",
    artifact: "docs/",
  },
  {
    id: "dashboard-agent",
    domain: "platform",
    name: "dashboard-agent",
    status: "working",
    priority: "P1",
    task: "Roadmap, agent monitor, схема взаимодействия",
    input: "Прогресс задач, статусы агентов",
    output: "Локальный dashboard и визуальная схема",
    training: "Нужно закрепить UI-правила и формат статусов",
    skills: "web-design-guidelines, webapp-testing, agent-browser",
    artifact: "dashboard/tasks/",
  },
  {
    id: "storage-agent",
    domain: "platform",
    name: "storage-agent",
    status: "done",
    priority: "P0",
    task: "config.py, storage.py, safe local file IO",
    input: "Файлы, JSON/YAML, raw-изображения",
    output: "Безопасные записи внутри проекта",
    training: "Обучен на правилах path boundary и JSON contracts",
    skills: "systematic-debugging",
    artifact: "src/running_coach/storage.py",
  },
  {
    id: "running-intake-agent",
    domain: "running",
    name: "running-intake-agent",
    status: "training",
    priority: "P1",
    task: "Классификация команд, фото и вопросов",
    input: "Telegram-команды, подписи, текст",
    output: "Маршрут: save/extract/qa/feedback",
    training: "Следующий: примеры фраз и intent-схема",
    skills: "local intent fixtures",
    artifact: "prompts/running_intake.md",
  },
  {
    id: "running-data-agent",
    domain: "running",
    name: "running-data-agent",
    status: "working",
    priority: "P0",
    task: "Сохранение тренировок и parsed.json",
    input: "Фото Telegram, история, vision JSON",
    output: "data/workouts/<date>/parsed.json",
    training: "Обучен частично: нужна политика нескольких тренировок в день",
    skills: "systematic-debugging",
    artifact: "schemas/workout.schema.json",
  },
  {
    id: "running-plan-agent",
    domain: "running",
    name: "running-plan-agent",
    status: "working",
    priority: "P0",
    task: "План дня и недели",
    input: "Профиль, история, календарь стартов",
    output: "current_training_plan.json и coaching_report.json",
    training: "Нужно обучить правилам адаптации после фидбэка",
    skills: "local coaching rules",
    artifact: "schemas/training_plan.schema.json",
  },
  {
    id: "running-qa-agent",
    domain: "running",
    name: "running-qa-agent",
    status: "planned",
    priority: "P2",
    task: "Ответы по бегу через компактный контекст",
    input: "Вопрос пользователя + compact context",
    output: "Короткий ответ тренера",
    training: "Нужно собрать context-pack и safety rules",
    skills: "local compact context",
    artifact: "prompts/running_qa.md",
  },
  {
    id: "llm-routing-agent",
    domain: "platform",
    name: "llm-routing-agent",
    status: "working",
    priority: "P0",
    task: "OpenAI-compatible LLM client",
    input: "LLM_BASE_URL, модель, ключ",
    output: "Qwen/OpenAI-compatible вызовы",
    training: "Нужно закрепить retry/timeout/cost policy",
    skills: "systematic-debugging",
    artifact: "src/running_coach/llm.py",
  },
  {
    id: "nutrition-data-agent",
    domain: "nutrition",
    name: "nutrition-data-agent",
    status: "planned",
    priority: "P3",
    task: "Фото еды, предпочтения, дневник питания",
    input: "Фото еды, preferences.json",
    output: "meal.json и дневные summary",
    training: "Ждёт этап питания",
    skills: "local meal estimation",
    artifact: "schemas/meal.schema.json",
  },
  {
    id: "documentation-agent",
    domain: "platform",
    name: "documentation-agent",
    status: "done",
    priority: "P1",
    task: "Синхронизация README, AGENTS, CLAUDE, docs",
    input: "Изменения кода и решений",
    output: "Актуальные инструкции для Claude/Qwen/Codex",
    training: "Обучен на текущей структуре проекта",
    skills: "find-skills, skill-creator",
    artifact: "README.md",
  },
];

const agentPipeline = [
  ["PM", "project-manager-agent", "working"],
  ["Task routing", "project-orchestrator", "working"],
  ["Фото/текст", "running-intake-agent", "done"],
  ["Raw IO", "storage-agent", "done"],
  ["Данные тренировки", "running-data-agent", "working"],
  ["LLM/Vision", "llm-routing-agent", "working"],
  ["Аналитика", "running-plan-agent", "working"],
  ["Ответ пользователю", "running-qa-agent", "planned"],
];

const statusLabels = {
  planned: "Запланировано",
  active: "В работе",
  done: "Готово",
};

const agentStatusLabels = {
  done: "готово",
  working: "в работе",
  idle: "ожидает",
  planned: "план",
  blocked: "блокер",
  training: "обучение",
};

const roadmap = document.querySelector("#roadmap");
const template = document.querySelector("#stageTemplate");
const progressValue = document.querySelector("#progressValue");
const progressBar = document.querySelector("#progressBar");
const doneCount = document.querySelector("#doneCount");
const activeCount = document.querySelector("#activeCount");
const plannedCount = document.querySelector("#plannedCount");
const heroPhase = document.querySelector("#heroPhase");
const heroTitle = document.querySelector("#heroTitle");
const heroSubtitle = document.querySelector("#heroSubtitle");
const heroStats = document.querySelector("#heroStats");
const heroTimeline = document.querySelector("#heroTimeline");
const projectStatusSource = document.querySelector("#projectStatusSource");
const agentGrid = document.querySelector("#agentGrid");
const agentKpis = document.querySelector("#agentKpis");
const agentPipelineEl = document.querySelector("#agentPipeline");
const agentMatrix = document.querySelector("#agentMatrix");
const agentUpdated = document.querySelector("#agentUpdated");
const agentEvents = document.querySelector("#agentEvents");
const botRuntime = document.querySelector("#botRuntime");
const themeToggle = document.querySelector("#themeToggle");

let progress = loadProgress();
let activeTaskIds = [];
let projectStatus = null;
let currentFilter = "all";
let currentAgentFilter = "all";

applyTheme(loadTheme());
renderRoadmap();
renderAgents();
updateSummary();
renderHero();
bindEvents();
loadRuntimeData();
setInterval(loadRuntimeData, RUNTIME_REFRESH_MS);

function bindEvents() {
  document.addEventListener("click", (event) => {
    const mainTab = event.target.closest("[data-view]");
    if (mainTab) {
      const target = mainTab.dataset.view;
      document.querySelectorAll("[data-view]").forEach((item) => {
        item.classList.toggle("is-active", item === mainTab);
      });
      document.querySelectorAll("[data-panel]").forEach((panel) => {
        panel.classList.toggle("is-active", panel.dataset.panel === target);
      });
      return;
    }

    const filterButton = event.target.closest("[data-filter]");
    if (filterButton) {
      currentFilter = filterButton.dataset.filter;
      document.querySelectorAll("[data-filter]").forEach((item) => {
        item.classList.toggle("is-active", item === filterButton);
      });
      applyFilter();
      return;
    }

    const agentFilterButton = event.target.closest("[data-agent-filter]");
    if (agentFilterButton) {
      currentAgentFilter = agentFilterButton.dataset.agentFilter;
      document.querySelectorAll("[data-agent-filter]").forEach((item) => {
        item.classList.toggle("is-active", item === agentFilterButton);
      });
      renderAgents();
      return;
    }

    if (event.target.closest("#resetProgress")) {
      progress = { ...DEFAULT_DONE };
      activeTaskIds = [];
      projectStatus = null;
      saveProgress();
      renderRoadmap();
      updateSummary();
      renderHero();
      return;
    }

    if (event.target.closest("#themeToggle")) {
      const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      applyTheme(nextTheme);
      localStorage.setItem(THEME_KEY, nextTheme);
    }
  });
}

function renderRoadmap() {
  roadmap.innerHTML = "";

  stages.forEach((stage) => {
    const node = template.content.firstElementChild.cloneNode(true);
    const status = getStageStatus(stage);

    node.dataset.stage = stage.id;
    node.dataset.status = status;
    node.querySelector(".stage-kicker").textContent = stage.number;
    node.querySelector("h3").textContent = stage.title;
    node.querySelector(".stage-description").textContent = stage.description;
    node.querySelector(".stage-duration").textContent = stage.duration;
    node.querySelector(".stage-usable").textContent = stage.usable;

    const statusPill = node.querySelector(".stage-status");
    statusPill.textContent = statusLabels[status];
    statusPill.className = `stage-status ${status}`;

    const list = node.querySelector(".task-list");
    stage.tasks.forEach(([taskId, label, tag]) => {
      const fullId = `${stage.id}:${taskId}`;
      const item = document.createElement("li");
      const checked = Boolean(progress[fullId]);
      item.className = `task-item${checked ? " is-done" : ""}`;

      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.id = fullId;
      checkbox.checked = checked;
      checkbox.addEventListener("change", () => {
        if (checkbox.checked) {
          progress[fullId] = true;
        } else {
          delete progress[fullId];
        }
        saveProgress();
        renderRoadmap();
        updateSummary();
      });

      const text = document.createElement("label");
      text.htmlFor = fullId;
      text.textContent = label;

      const badge = document.createElement("span");
      badge.className = "task-tag";
      badge.textContent = tag;

      item.append(checkbox, text, badge);
      list.append(item);
    });

    roadmap.append(node);
  });

  applyFilter();
}

function renderAgents() {
  agentGrid.innerHTML = "";
  agentKpis.innerHTML = "";
  agentPipelineEl.innerHTML = "";
  agentMatrix.innerHTML = "";

  const visibleAgents = agents.filter((agent) => matchAgentFilter(agent));
  const counts = agents.reduce(
    (acc, agent) => {
      acc.total += 1;
      acc[agent.status] = (acc[agent.status] || 0) + 1;
      return acc;
    },
    { total: 0 }
  );

  [
    ["Всего агентов", counts.total, "platform"],
    ["Готовы", counts.done || 0, "done"],
    ["В работе", counts.working || 0, "working"],
    ["К обучению", (counts.training || 0) + (counts.planned || 0), "training"],
  ].forEach(([label, value, tone]) => {
    const item = document.createElement("article");
    item.className = `agent-kpi ${tone}`;
    item.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
    agentKpis.append(item);
  });

  visibleAgents.forEach((agent) => {
    const card = document.createElement("article");
    card.className = `agent-card ${agent.status}`;
    card.dataset.domain = agent.domain;
    card.innerHTML = `
      <div class="agent-card-head">
        <div>
          <h3>${agent.name}</h3>
          <div class="agent-domain">${domainLabel(agent.domain)} · ${agent.priority}</div>
        </div>
        <span class="agent-status ${agent.status}">${agentStatusLabels[agent.status]}</span>
      </div>
      <p>${agent.task}</p>
      <dl class="agent-io">
        <div><dt>Вход</dt><dd>${agent.input}</dd></div>
        <div><dt>Выход</dt><dd>${agent.output}</dd></div>
      </dl>
      <div class="agent-skills"><span>Skills</span>${agent.skills}</div>
      <div class="agent-training">${agent.training}</div>
      <div class="agent-artifact">${agent.artifact}</div>
    `;
    agentGrid.append(card);
  });

  agentPipeline.forEach(([label, agentName, state], index) => {
    const step = document.createElement("div");
    step.className = `pipe-step ${state}`;
    step.innerHTML = `<span>${label}</span><strong>${agentName}</strong>`;
    agentPipelineEl.append(step);
    if (index < agentPipeline.length - 1) {
      const arrow = document.createElement("div");
      arrow.className = `pipe-arrow ${state}`;
      arrow.textContent = "→";
      agentPipelineEl.append(arrow);
    }
  });

  agents.forEach((agent) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td><strong>${agent.name}</strong><br><span>${domainLabel(agent.domain)} · ${agentStatusLabels[agent.status]}</span></td>
      <td>${agent.task}</td>
      <td>${agent.input}</td>
      <td>${agent.output}</td>
      <td>${agent.skills}</td>
      <td>${agent.training}</td>
    `;
    agentMatrix.append(row);
  });
}

function renderHero() {
  const summary = progressSummary();
  const currentStage = stageById(projectStatus?.current_stage_id) || currentActiveStage() || stages[0];
  const nextTask = projectStatus?.next_task || nextVisibleTask(currentStage) || "Следующая задача уточняется PM-агентом.";

  if (heroPhase) {
    heroPhase.textContent = projectStatus?.phase || stageLabel(currentStage);
  }
  if (heroTitle) {
    heroTitle.textContent = projectStatus?.headline || currentStage.title;
  }
  if (heroSubtitle) {
    heroSubtitle.textContent = projectStatus?.summary || `${currentStage.description} Следующий шаг: ${nextTask}`;
  }

  if (heroStats) {
    const stats = Array.isArray(projectStatus?.hero_stats)
      ? projectStatus.hero_stats
      : [
          { value: `${summary.percent}%`, label: "roadmap готов", tone: "accent" },
          { value: summary.doneStages, label: "этапов закрыто", tone: "success" },
          { value: summary.activeStages, label: "этапов в работе", tone: "info" },
          { value: activeTaskIds.length || "0", label: "активных задач", tone: "warn" },
        ];
    heroStats.innerHTML = "";
    stats.forEach((stat) => {
      const item = document.createElement("div");
      item.className = "hero-stat";
      item.innerHTML = `
        <div class="hero-stat-val ${stat.tone || "accent"}">${stat.value}</div>
        <div class="hero-stat-lab">${stat.label}</div>
      `;
      heroStats.append(item);
    });
  }

  if (heroTimeline) {
    heroTimeline.innerHTML = "";
    compactTimelineStages().forEach((stage) => {
      const status = getStageStatus(stage);
      const isCurrent = stage.id === currentStage.id;
      const item = document.createElement("div");
      item.className = `ht-item ${timelineClass(status, isCurrent)}`;
      item.innerHTML = `
        <div class="ht-dot ${timelineClass(status, isCurrent)}">${stage.number.replace(/\D/g, "") || "•"}</div>
        <div class="ht-name ${isCurrent ? "active" : ""}">${shortStageName(stage)}</div>
        <div class="ht-period">${isCurrent ? "сейчас" : stage.duration}</div>
      `;
      heroTimeline.append(item);
    });
  }
}

async function loadRuntimeData() {
  await Promise.all([loadProjectStatus(), loadAgentStatus(), loadAgentEvents(), loadBotStatus()]);
}

async function loadProjectStatus() {
  try {
    const response = await fetch("/api/project-status", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`project status ${response.status}`);
    }
    const data = await response.json();
    if (Array.isArray(data.done_task_ids)) {
      const nextProgress = {};
      data.done_task_ids.forEach((taskId) => {
        nextProgress[taskId] = true;
      });
      projectStatus = data;
      activeTaskIds = Array.isArray(data.active_task_ids) ? data.active_task_ids : [];
      progress = nextProgress;
      renderRoadmap();
      updateSummary();
      renderHero();
      updateProjectStatusSource("project_status.json", data.updated_at);
    }
  } catch {
    updateProjectStatusSource("fallback", null);
    // Keep browser-local progress when the file-backed status is unavailable.
  }
}

async function loadAgentStatus() {
  try {
    const response = await fetch("/api/agent-status", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`agent status ${response.status}`);
    }
    const data = await response.json();
    if (Array.isArray(data.agents)) {
      agents = mergeAgents(agents, data.agents);
      renderAgents();
    }
    if (agentUpdated) {
      agentUpdated.textContent = `Обновлено: ${formatDateTime(data.updated_at)}`;
    }
  } catch {
    if (agentUpdated) {
      agentUpdated.textContent = "Live-статусы недоступны, показана встроенная версия";
    }
  }
}

async function loadAgentEvents() {
  if (!agentEvents) {
    return;
  }
  try {
    const response = await fetch("/api/agent-events", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`agent events ${response.status}`);
    }
    const text = await response.text();
    const events = text
      .split(/\r?\n/)
      .filter(Boolean)
      .map((line) => JSON.parse(line))
      .slice(-8)
      .reverse();
    renderAgentEvents(events);
  } catch {
    agentEvents.innerHTML = `<div class="agent-event muted">Журнал событий пока пуст</div>`;
  }
}

async function loadBotStatus() {
  if (!botRuntime) {
    return;
  }
  try {
    const response = await fetch("/api/bot-status", { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`bot status ${response.status}`);
    }
    const data = await response.json();
    botRuntime.className = `runtime-status ${data.status || "down"}`;
    botRuntime.textContent = `Бот: ${runtimeLabel(data.status)}${
      data.pid ? ` · PID ${data.pid}` : ""
    }`;
  } catch {
    botRuntime.className = "runtime-status down";
    botRuntime.textContent = "Бот: статус недоступен";
  }
}

function runtimeLabel(status) {
  const labels = {
    running: "жив",
    stale_pid: "устаревший PID",
    down: "не запущен",
  };
  return labels[status] || "неизвестно";
}

function mergeAgents(baseAgents, runtimeAgents) {
  const byName = new Map(baseAgents.map((agent) => [agent.name, agent]));
  runtimeAgents.forEach((runtimeAgent) => {
    const existing = byName.get(runtimeAgent.name);
    if (existing) {
      Object.assign(existing, compactRuntimeAgent(runtimeAgent));
    } else {
      byName.set(runtimeAgent.name, {
        id: runtimeAgent.name,
        domain: runtimeAgent.domain || "platform",
        priority: runtimeAgent.priority || "P2",
        input: runtimeAgent.input || "local data",
        output: runtimeAgent.output || "updated status",
        training: runtimeAgent.training || "runtime status",
        skills: runtimeAgent.skills || "local instructions",
        ...compactRuntimeAgent(runtimeAgent),
      });
    }
  });
  return Array.from(byName.values());
}

function compactRuntimeAgent(agent) {
  return Object.fromEntries(
    Object.entries(agent).filter(([, value]) => value !== undefined && value !== null && value !== "")
  );
}

function renderAgentEvents(events) {
  if (!events.length) {
    agentEvents.innerHTML = `<div class="agent-event muted">Журнал событий пока пуст</div>`;
    return;
  }
  agentEvents.innerHTML = "";
  events.forEach((event) => {
    const item = document.createElement("article");
    item.className = `agent-event ${event.event || "info"}`;
    item.innerHTML = `
      <span>${formatDateTime(event.ts)}</span>
      <strong>${event.agent || "agent"}</strong>
      <p>${event.task || event.event || "event"}</p>
      <code>${event.artifact || ""}</code>
    `;
    agentEvents.append(item);
  });
}

function formatDateTime(value) {
  if (!value) {
    return "нет данных";
  }
  try {
    return new Intl.DateTimeFormat("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(value));
  } catch {
    return value;
  }
}

function matchAgentFilter(agent) {
  if (currentAgentFilter === "all") {
    return true;
  }
  if (currentAgentFilter === "ready") {
    return agent.status === "done" || agent.status === "working";
  }
  if (currentAgentFilter === "training") {
    return agent.status === "training" || agent.status === "planned";
  }
  return agent.domain === currentAgentFilter;
}

function domainLabel(domain) {
  const labels = {
    running: "Бег",
    platform: "Платформа",
    nutrition: "Питание",
  };
  return labels[domain] || domain;
}

function getStageStatus(stage) {
  const total = stage.tasks.length;
  const done = stage.tasks.filter(([taskId]) => progress[`${stage.id}:${taskId}`]).length;

  if (done === total) {
    return "done";
  }

  if (
    done > 0 ||
    stage.status === "active" ||
    activeTaskIds.some((taskId) => taskId.startsWith(`${stage.id}:`))
  ) {
    return "active";
  }

  return stage.status;
}

function progressSummary() {
  const allTasks = stages.flatMap((stage) =>
    stage.tasks.map(([taskId]) => `${stage.id}:${taskId}`)
  );
  const done = allTasks.filter((taskId) => progress[taskId]).length;
  const percent = Math.round((done / allTasks.length) * 100);
  const counts = stages.reduce(
    (acc, stage) => {
      acc[getStageStatus(stage)] += 1;
      return acc;
    },
    { done: 0, active: 0, planned: 0 }
  );

  return {
    allTasks,
    doneTasks: done,
    totalTasks: allTasks.length,
    percent,
    doneStages: counts.done,
    activeStages: counts.active,
    plannedStages: counts.planned,
  };
}

function updateSummary() {
  const summary = progressSummary();
  progressValue.textContent = `${summary.percent}%`;
  progressBar.style.width = `${summary.percent}%`;
  doneCount.textContent = summary.doneStages;
  activeCount.textContent = summary.activeStages;
  plannedCount.textContent = summary.plannedStages;
}

function applyFilter() {
  document.querySelectorAll(".stage-card").forEach((card) => {
    const status = card.dataset.status;
    const isSoon = ["foundation", "running-bot-mvp", "plan-basic"].includes(card.dataset.stage);
    const visible =
      currentFilter === "all" ||
      status === currentFilter ||
      (currentFilter === "soon" && isSoon && status !== "done");

    card.classList.toggle("is-hidden", !visible);
  });
}

function loadProgress() {
  try {
    return { ...DEFAULT_DONE, ...(JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}) };
  } catch {
    return { ...DEFAULT_DONE };
  }
}

function saveProgress() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(progress));
}

function loadTheme() {
  return localStorage.getItem(THEME_KEY) || "dark";
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  themeToggle.textContent = theme === "dark" ? "Светлая" : "Темная";
}

function updateProjectStatusSource(source, updatedAt) {
  if (!projectStatusSource) {
    return;
  }
  const stamp = updatedAt ? ` · ${formatDateTime(updatedAt)}` : "";
  projectStatusSource.textContent = `Источник прогресса: ${source}${stamp}`;
}

function stageById(stageId) {
  return stages.find((stage) => stage.id === stageId) || null;
}

function currentActiveStage() {
  return (
    stages.find((stage) => getStageStatus(stage) === "active") ||
    stages.find((stage) => getStageStatus(stage) !== "done") ||
    stages[0]
  );
}

function nextVisibleTask(stage) {
  const activeTask = activeTaskIds.find((taskId) => taskId.startsWith(`${stage.id}:`));
  if (activeTask) {
    return taskLabel(activeTask);
  }
  const task = stage.tasks.find(([taskId]) => !progress[`${stage.id}:${taskId}`]);
  return task ? task[1] : null;
}

function taskLabel(fullTaskId) {
  const [stageId, taskId] = fullTaskId.split(":");
  const stage = stageById(stageId);
  const task = stage?.tasks.find(([candidate]) => candidate === taskId);
  return task ? task[1] : fullTaskId;
}

function compactTimelineStages() {
  const ids = ["foundation", "running-bot-mvp", "plan-basic", "llm-context", "schedule", "nutrition"];
  return ids.map(stageById).filter(Boolean);
}

function timelineClass(status, isCurrent) {
  if (isCurrent || status === "active") {
    return "active";
  }
  if (status === "done") {
    return "done";
  }
  return "todo";
}

function stageLabel(stage) {
  return `${stage.number}: ${shortStageName(stage)}`;
}

function shortStageName(stage) {
  const labels = {
    foundation: "Фундамент",
    "running-bot-mvp": "Бот",
    "plan-basic": "План",
    "llm-context": "LLM/QA",
    schedule: "Режим",
    nutrition: "Питание",
    "reports-dashboard": "Dashboard",
    "infra-migration": "Инфра",
  };
  return labels[stage.id] || stage.title;
}
