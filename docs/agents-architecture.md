# Иерархия агентов Running Coach

Дата: 2026-05-12  
Статус: проектная структура  
Цель документа: определить агентов, субагентов, зоны ответственности и последовательность выполнения задач.

Связанный документ: `docs/agent-training-plan.md`. В нем указано, какие навыки и external skills нужны каждому агенту.

## 1. Принципы

### 1.1 Иерархия вместо хаоса

Проект должен развиваться через понятную цепочку агентов:

1. управляющий агент принимает задачу;
2. определяет домен;
3. передает работу профильному агенту;
4. профильный агент вызывает нужных субагентов;
5. результат возвращается наверх в структурированном виде;
6. пользователь получает короткий понятный ответ.

### 1.2 Один агент - одна зона ответственности

Агент не должен делать все сразу. Например, агент приема тренировок не должен сам строить тренировочный план, а агент планирования не должен заниматься сохранением raw-файлов.

### 1.3 Файлы и JSON как контракт

Обмен между агентами в MVP должен идти через файлы и структурированные JSON-объекты. Это проще для отладки, переносимости и будущей миграции в Postgres/Redis.

### 1.4 Последовательность важнее параллельности

На раннем этапе задачи выполняются последовательно. Параллельность добавляется позже только там, где она действительно нужна.

### 1.5 Каждый агент должен быть обучаемым

Для каждого агента нужно фиксировать:

- роль;
- ответственность;
- границы ответственности;
- входы;
- выходы;
- навыки;
- назначенные skills;
- субагентов, если есть.

Skills не являются обязательными для каждого агента. Если надежного external skill нет, агент получает локальную инструкцию в `AGENTS.md`, `CLAUDE.md`, `prompts/` или отдельном проектном skill.

### 1.6 Qwen как провайдер, а не жесткая зависимость

Qwen подключается через OpenAI-compatible endpoint и принадлежит зоне ответственности `llm-routing-agent`. Доменные агенты не должны знать конкретный SDK или фреймворк Qwen: они передают задачу, prompt, компактный контекст и ожидаемый формат результата.

На этапе MVP агентность реализуется простыми Python workflow, JSON-контрактами, файлами и prompt-файлами. CrewAI, LangGraph, Qwen-Agent или другой агентский фреймворк можно добавлять позже, когда локальная Telegram-петля уже стабильна и фреймворк действительно уменьшает сложность.

### 1.7 Безопасность LLM-интеграций

- API-ключи хранятся только локально и не попадают в prompts, dashboard, Telegram-ответы или логи.
- Нельзя вводить ключи Qwen, Claude, OpenAI или других провайдеров в непроверенные агентские платформы.
- Raw-изображения отправляются в vision-модель только для первичного извлечения; дальше агенты работают с `parsed.json`, summaries и планом.
- Длинный контекст Qwen не отменяет правило компактного контекста: в запрос передается только то, что нужно для конкретного решения.

## 2. Верхний уровень

```text
project-manager-agent
  project-orchestrator
    running-domain-agent
      running-intake-agent
      running-data-agent
      running-plan-agent
      running-schedule-agent
      running-qa-agent
      running-report-agent
    nutrition-domain-agent
      nutrition-intake-agent
      nutrition-data-agent
      nutrition-plan-agent
      grocery-agent
      nutrition-qa-agent
    platform-domain-agent
      storage-agent
      llm-routing-agent
      dashboard-agent
      deployment-agent
      documentation-agent
```

## 3. `project-orchestrator`

### Назначение

Главный управляющий агент проекта. Он не выполняет доменную работу сам, а маршрутизирует задачи между агентами и следит за последовательностью.

### Ответственность

- принять входящее событие или задачу;
- определить тип задачи;
- выбрать доменный агент;
- проверить, что есть нужные входные данные;
- собрать итоговый результат;
- вернуть пользователю ответ;
- записать статус задачи в roadmap/лог.

### Не отвечает за

- OCR;
- тренировочные рекомендации;
- нутрициологические рекомендации;
- сохранение файлов напрямую;
- генерацию dashboard.

### Входы

- Telegram update;
- CLI-команда;
- scheduled event;
- ручная задача от пользователя;
- файл, добавленный в проект.

### Выходы

```json
{
  "task_id": "2026-05-12-running-photo-001",
  "domain": "running",
  "status": "completed",
  "result_summary": "Workout image saved and parsed draft created.",
  "artifacts": []
}
```

## 4. Running domain

## 4.1 `running-domain-agent`

### Назначение

Координатор всех задач, связанных с бегом.

### Ответственность

- принимать задачи от `project-orchestrator`;
- выбирать нужный running-субагент;
- контролировать цепочку: intake -> data -> plan -> response;
- не допускать смешивания данных тренировок и питания;
- готовить короткий итог для пользователя.

### Типовые задачи

- новое фото тренировки;
- вопрос по бегу;
- запрос плана на день;
- запрос плана на неделю;
- перенос тренировки;
- воскресный отчет.

## 4.2 `running-intake-agent`

### Назначение

Первичный прием пользовательских сообщений в беговом боте.

### Ответственность

- классифицировать входящее Telegram-сообщение;
- понять, это команда, фото, вопрос или изменение плана;
- извлечь подпись к фото;
- определить предварительную дату тренировки;
- передать данные следующему агенту.

### Входы

- Telegram message;
- message text;
- photo metadata;
- caption.

### Выходы

```json
{
  "type": "workout_photo",
  "source": "telegram",
  "date_hint": "2026-05-12",
  "caption": "Сегодня легкая 5 км",
  "requires_confirmation": false
}
```

### Не отвечает за

- сохранение файла;
- OCR;
- тренировочные рекомендации.

## 4.3 `running-data-agent`

### Назначение

Хранение и нормализация данных тренировок.

### Ответственность

- сохранять raw-файлы в `data/workouts/<date>/raw`;
- создавать директории;
- не перезаписывать файлы;
- создавать или обновлять `parsed.json`;
- хранить относительные пути;
- проверять, что операции остаются внутри project root;
- запускать OCR/vision flow после MVP.

### Субагенты

#### `workout-file-agent`

Отвечает только за файловые операции:

- создать папку тренировки;
- выбрать уникальное имя файла;
- сохранить raw-файл;
- вернуть относительный путь.

#### `workout-parser-agent`

Отвечает за извлечение структурированных данных:

- дата;
- дистанция;
- длительность;
- темп;
- пульс;
- высота;
- каденс;
- confidence.

В MVP может создавать черновой `parsed.json` с `null` в неизвестных полях.

#### `workout-validation-agent`

Проверяет данные:

- дистанция не отрицательная;
- длительность согласуется с темпом;
- дата валидна;
- raw-файлы существуют;
- confidence указан после OCR/vision.

### Выход

```json
{
  "workout_id": "2026-05-12-run-001",
  "date": "2026-05-12",
  "raw_files": ["data/workouts/2026-05-12/raw/telegram_001.jpg"],
  "parsed_path": "data/workouts/2026-05-12/parsed.json",
  "status": "saved"
}
```

## 4.4 `running-plan-agent`

### Назначение

Создание и корректировка тренировочного плана.

### Ответственность

- читать профиль спортсмена;
- читать историю тренировок;
- строить план дня/недели;
- корректировать план после пропусков;
- учитывать ограничения и признаки усталости;
- контролировать рост недельного объема;
- генерировать структурированный план.

### Субагенты

#### `profile-analysis-agent`

Анализирует профиль:

- возраст;
- рост/вес;
- пульсовые зоны;
- цели;
- ограничения;
- доступные дни.

#### `training-load-agent`

Считает нагрузку:

- недельный объем;
- количество тренировок;
- интенсивность;
- динамику темпа и пульса;
- пропуски;
- резкие скачки нагрузки.

#### `plan-builder-agent`

Создает план:

- типы тренировок;
- длительность;
- дистанция;
- целевой пульс;
- темп;
- инструкции.

#### `plan-safety-agent`

Проверяет план на риски:

- слишком быстрый рост объема;
- слишком много интенсивных дней;
- нет дней отдыха;
- конфликт с ограничениями пользователя.

### Выход

```json
{
  "week_start": "2026-05-11",
  "week_end": "2026-05-17",
  "days": [],
  "warnings": [],
  "status": "ready"
}
```

## 4.5 `running-schedule-agent`

### Назначение

Расписание и напоминания.

### Ответственность

- читать `data/schedule.yaml`;
- отправлять утренний план;
- запускать воскресный отчет;
- замечать пропущенные тренировки;
- инициировать корректировку плана.

### Субагенты

#### `morning-reminder-agent`

Отправляет план дня.

#### `weekly-review-trigger-agent`

Запускает недельную аналитику и план следующей недели.

#### `missed-workout-agent`

Проверяет, была ли загружена тренировка после запланированного дня.

## 4.6 `running-qa-agent`

### Назначение

Ответы на вопросы по бегу.

### Ответственность

- принять вопрос;
- собрать компактный контекст;
- вызвать LLM;
- вернуть Telegram-friendly ответ;
- не использовать raw-изображения без необходимости.

### Субагенты

#### `running-context-agent`

Собирает:

- профиль;
- план текущей недели;
- последние 7-14 дней тренировок;
- последнюю weekly summary.

#### `running-answer-agent`

Формирует ответ через LLM.

#### `answer-safety-agent`

Проверяет:

- нет ли медицинских обещаний;
- нет ли агрессивных рекомендаций;
- есть ли предупреждение при боли, травме, сильной усталости.

## 4.7 `running-report-agent`

### Назначение

Отчеты и аналитика.

### Ответственность

- недельная сводка;
- динамика объема;
- динамика темпа;
- динамика пульса;
- compliance с планом;
- подготовка данных для dashboard и Excel.

### Субагенты

#### `weekly-summary-agent`

Создает `data/derived/weekly_summaries.jsonl`.

#### `excel-report-agent`

Генерирует `reports/training_plan.xlsx` после MVP.

#### `dashboard-data-agent`

Готовит JSON для `dashboard/app`.

## 5. Nutrition domain

## 5.1 `nutrition-domain-agent`

### Назначение

Координатор питания.

### Ответственность

- принимать задачи питания;
- учитывать тренировочный план;
- передавать фото еды на оценку;
- обновлять дневник питания;
- запускать grocery-flow.

## 5.2 `nutrition-intake-agent`

Классифицирует сообщения:

- фото еды;
- вопрос по питанию;
- список покупок;
- уточнение порции;
- команда.

## 5.3 `nutrition-data-agent`

### Ответственность

- сохранять фото еды;
- создавать JSON приема пищи;
- хранить диапазоны калорий и БЖУ;
- задавать уточняющие вопросы при низкой уверенности.

### Субагенты

#### `meal-file-agent`

Сохраняет raw-фото еды.

#### `meal-estimation-agent`

Оценивает:

- продукты;
- граммы;
- калории;
- белки;
- жиры;
- углеводы;
- confidence.

#### `meal-validation-agent`

Следит, чтобы оценка была диапазоном и не выглядела ложной точностью.

## 5.4 `nutrition-plan-agent`

### Ответственность

- составлять дневной рацион;
- учитывать тренировку дня;
- учитывать уже съеденное;
- учитывать цели и ограничения;
- давать рекомендации на остаток дня.

### Субагенты

#### `daily-nutrition-agent`

План на день.

#### `weekly-menu-agent`

Меню на неделю.

#### `nutrition-adjustment-agent`

Корректировка после фактической еды.

## 5.5 `grocery-agent`

### Ответственность

- разбирать список покупок;
- вести `inventory.json`;
- отслеживать остатки;
- предлагать, что докупить.

### Субагенты

#### `inventory-agent`

Ведет остатки продуктов.

#### `shopping-list-agent`

Генерирует список покупок.

#### `grocery-reminder-agent`

Напоминает о продуктах ниже threshold.

## 5.6 `nutrition-qa-agent`

Отвечает на вопросы по питанию с учетом:

- профиля;
- тренировочного плана;
- дневника питания за сегодня;
- доступных продуктов;
- целей пользователя.

## 6. Platform domain

## 6.1 `platform-domain-agent`

Координирует технические задачи проекта.

### Ответственность

- структура проекта;
- конфиги;
- хранение;
- LLM routing;
- dashboard;
- деплой;
- документация.

## 6.2 `storage-agent`

### Назначение

Единый слой файлового хранения.

### Ответственность

- безопасные пути;
- чтение/запись YAML;
- чтение/запись JSON;
- атомарное сохранение файлов;
- миграция в Postgres после MVP.

### Субагенты

#### `schema-agent`

Поддерживает JSON Schema/Pydantic-модели.

#### `migration-agent`

Готовит перенос файловых данных в Postgres.

## 6.3 `llm-routing-agent`

### Ответственность

- выбирать модель;
- собирать request;
- ограничивать контекст;
- логировать ошибки;
- применять fallback.

### Routing

- Qwen: default;
- DeepSeek: сложный reasoning;
- Claude: ручное ревью и редкие high-value задачи;
- vision model: изображения.

## 6.4 `dashboard-agent`

### Ответственность

- roadmap page;
- project dashboard;
- спортивный dashboard;
- данные для графиков;
- подготовка к Vercel.

## 6.5 `documentation-agent`

### Ответственность

- `README.md`;
- `AGENTS.md`;
- `CLAUDE.md`;
- `docs/project-goals.md`;
- `docs/technical-spec.md`;
- changelog.

## 6.6 `deployment-agent`

### Ответственность после MVP

- Vercel для frontend/dashboard;
- VDS для bot/backend;
- `.env` management;
- HTTPS;
- backups;
- firewall;
- health checks.

## 7. Последовательности выполнения

## 7.1 Новое фото тренировки

```text
project-orchestrator
  -> running-domain-agent
    -> running-intake-agent
    -> running-data-agent
      -> workout-file-agent
      -> workout-parser-agent
      -> workout-validation-agent
    -> running-plan-agent, если тренировка влияет на план
    -> running-domain-agent: короткий ответ пользователю
```

Результат:

- raw-файл сохранен;
- `parsed.json` создан или обновлен;
- пользователь получил подтверждение.

## 7.2 Запрос `/today`

```text
project-orchestrator
  -> running-domain-agent
    -> running-plan-agent
      -> profile-analysis-agent
    -> running-domain-agent: Telegram response
```

Результат:

- пользователь видит план на текущий день.

## 7.3 Запрос `/week`

```text
project-orchestrator
  -> running-domain-agent
    -> running-plan-agent
      -> plan-builder-agent, если плана нет
      -> plan-safety-agent
    -> running-domain-agent: Telegram response
```

Результат:

- пользователь видит недельный план.

## 7.4 Вопрос по бегу

```text
project-orchestrator
  -> running-domain-agent
    -> running-qa-agent
      -> running-context-agent
      -> running-answer-agent
      -> answer-safety-agent
    -> running-domain-agent: Telegram response
```

Результат:

- пользователь получает ответ с учетом профиля и плана.

## 7.5 Пропуск тренировки

```text
project-orchestrator
  -> running-domain-agent
    -> running-intake-agent
    -> running-schedule-agent
      -> missed-workout-agent
    -> running-plan-agent
      -> training-load-agent
      -> plan-builder-agent
      -> plan-safety-agent
    -> running-domain-agent: обновленный план
```

Результат:

- план скорректирован без резкого увеличения нагрузки.

## 7.6 Фото еды

```text
project-orchestrator
  -> nutrition-domain-agent
    -> nutrition-intake-agent
    -> nutrition-data-agent
      -> meal-file-agent
      -> meal-estimation-agent
      -> meal-validation-agent
    -> nutrition-plan-agent
      -> nutrition-adjustment-agent
    -> nutrition-domain-agent: рекомендации
```

Результат:

- фото еды сохранено;
- создан JSON приема пищи;
- пользователь получил диапазон калорий/БЖУ и рекомендацию.

## 7.7 Воскресный отчет

```text
project-orchestrator
  -> running-domain-agent
    -> running-schedule-agent
      -> weekly-review-trigger-agent
    -> running-report-agent
      -> weekly-summary-agent
    -> running-plan-agent
      -> training-load-agent
      -> plan-builder-agent
      -> plan-safety-agent
    -> running-domain-agent: weekly report + next week plan
```

Результат:

- создан weekly summary;
- создан план следующей недели;
- пользователь получил отчет.

## 8. Приоритет внедрения агентов

### MVP

Нужны сразу:

1. `project-orchestrator`;
2. `running-domain-agent`;
3. `running-intake-agent`;
4. `running-data-agent`;
5. `workout-file-agent`;
6. `running-plan-agent`;
7. `running-qa-agent`;
8. `running-context-agent`;
9. `llm-routing-agent`;
10. `storage-agent`;
11. `documentation-agent`.

### После первого запуска

Добавить:

1. `workout-parser-agent`;
2. `workout-validation-agent`;
3. `training-load-agent`;
4. `plan-builder-agent`;
5. `plan-safety-agent`;
6. `running-schedule-agent`;
7. `morning-reminder-agent`;
8. `weekly-summary-agent`.

### Полная версия

Добавить:

1. nutrition domain;
2. grocery domain;
3. dashboard agent;
4. deployment agent;
5. migration agent;
6. Excel/report agents;
7. Qdrant memory integration.

## 9. Правила взаимодействия агентов

### 9.1 Агент не пишет в чужую область

Примеры:

- `running-qa-agent` не должен сохранять тренировки;
- `nutrition-data-agent` не должен менять беговой план;
- `dashboard-agent` не должен менять исходные тренировочные данные;
- `llm-routing-agent` не должен принимать доменные решения.

### 9.2 Каждый агент возвращает структурированный результат

Минимальный формат:

```json
{
  "agent": "running-data-agent",
  "status": "completed",
  "summary": "Workout saved.",
  "artifacts": [],
  "warnings": [],
  "next_actions": []
}
```

### 9.3 Ошибки не скрывать

Если агент не может выполнить задачу:

- вернуть `status: "failed"`;
- указать причину;
- предложить следующий безопасный шаг;
- не выдумывать данные.

### 9.4 Raw-данные не отправлять повторно

Сырые изображения используются только для первичного распознавания. Дальше агенты должны работать со структурированными JSON и summary.

## 10. Итоговая схема ответственности

| Агент | Главная зона | Когда нужен |
|---|---|---|
| `project-orchestrator` | маршрутизация задач | всегда |
| `running-domain-agent` | беговой домен | MVP |
| `running-intake-agent` | классификация сообщений | MVP |
| `running-data-agent` | данные тренировок | MVP |
| `running-plan-agent` | планы тренировок | MVP |
| `running-qa-agent` | вопросы по бегу | MVP |
| `running-schedule-agent` | расписание | после MVP |
| `running-report-agent` | аналитика и отчеты | после MVP |
| `nutrition-domain-agent` | питание | полная версия |
| `grocery-agent` | продукты и покупки | полная версия |
| `storage-agent` | файловое хранение | MVP |
| `llm-routing-agent` | выбор моделей | MVP |
| `dashboard-agent` | web-панели | уже частично нужен |
| `documentation-agent` | документация | MVP |
| `deployment-agent` | деплой | после MVP |

## 11. `project-manager-agent`

### Назначение

`project-manager-agent` стоит над `project-orchestrator` и отвечает не за реализацию, а за управление ходом разработки: стадия проекта, ближайшая задача, блокеры, критерии приемки, статусы агентов и порядок передачи задач.

### Ответственность

- держать актуальным `docs/project-management.md`;
- выбирать следующий конкретный шаг разработки;
- фиксировать, на какой стадии находится проект и что уже можно использовать;
- определять владельца задачи среди агентов;
- задавать критерии готовности до начала реализации;
- отмечать блокеры и отложенные решения;
- обновлять `data/derived/agent_status.json`;
- следить, чтобы dashboard показывал реальное состояние проекта;
- использовать `find-skills` перед добавлением новых внешних skills.

### Не отвечает за

- написание кода Telegram-бота;
- тренировочные рекомендации;
- распознавание фото;
- настройку LLM-провайдера;
- дизайн dashboard;
- деплой.

### Входы

- решения пользователя;
- roadmap и task dashboard;
- `docs/project-goals.md`;
- `docs/technical-spec.md`;
- `docs/agent-training-status.md`;
- `docs/skills-training-map.md`;
- `data/derived/agent_status.json`;
- `data/derived/agent_events.jsonl`.

### Выходы

```json
{
  "owner": "running-plan-agent",
  "task": "Add safe plan adjustment after actual-vs-planned mismatch.",
  "status": "ready_for_implementation",
  "acceptance": [
    "Mismatch is detected",
    "Coach review is saved",
    "Telegram summary is short",
    "Full plan is not blindly overwritten"
  ],
  "blockers": []
}
```

### Обучение и skills

- `find-skills` - поиск и оценка skills перед установкой;
- `systematic-debugging` - разбор блокеров по фактам;
- `skill-creator` - будущий локальный PM-skill, если процесс повторяется часто.

На 2026-05-13 отдельный внешний PM-skill не установлен: найденные через `find-skills` project-management/roadmap candidates имеют слабые install count относительно рекомендуемого порога, поэтому PM-агент обучен локальными проектными правилами.
