# Pixel Agents: проверка безопасности и установка

Дата проверки: 2026-05-12  
Репозиторий: https://github.com/pablodelucca/pixel-agents  
Marketplace: https://marketplace.visualstudio.com/items?itemName=pablodelucca.pixel-agents

## 1. Что это

Pixel Agents - расширение для VS Code, которое визуализирует Claude Code агентов как персонажей в pixel-art офисе.

Оно работает наблюдательно:

- запускает Claude Code терминалы из VS Code;
- читает JSONL-транскрипты Claude Code из `~/.claude/projects/...`;
- по событиям инструментов показывает, что агент читает, пишет, запускает команды или ждет пользователя;
- показывает sub-agents как отдельных персонажей.

## 2. Проверка безопасности

По README, Marketplace и исходникам расширение выглядит допустимым к использованию, но с важными ограничениями.

### Что делает расширение

- Создает VS Code terminal и запускает `claude --session-id <uuid>`.
- Читает локальные JSONL-файлы Claude Code.
- Сохраняет layout в пользовательских настройках и `~/.pixel-agents`.
- Может подключать внешние директории с asset-паками.
- Может запускать Claude Code с флагом `--dangerously-skip-permissions`, если выбрать соответствующий пункт UI.

### Основные риски

1. **Доступ к транскриптам Claude Code**  
   Расширение читает JSONL-файлы с историей работы Claude. Если в диалогах есть секреты, они могут отображаться или обрабатываться расширением локально.

2. **Запуск терминалов**  
   Кнопка `+ Agent` создает новый Claude terminal. Это ожидаемое поведение, но нужно понимать, что это запускает реального агента.

3. **Опасный режим permissions bypass**  
   В UI есть запуск с `--dangerously-skip-permissions`. Этот режим отключает запросы разрешений Claude Code. Для этого проекта его использовать нельзя.

4. **External asset directories**  
   Расширение может загружать custom assets из внешних папок. Использовать только доверенные локальные папки.

5. **Зависимость от VS Code и Claude Code**  
   Расширение не визуализирует Codex Desktop напрямую. Оно работает с Claude Code в VS Code.

## 3. Вердикт

Можно использовать для визуализации работы Claude Code агентов, если соблюдать правила:

- устанавливать только `pablodelucca.pixel-agents` из VS Code Marketplace или Open VSX;
- не включать `--dangerously-skip-permissions`;
- не добавлять неизвестные external asset directories;
- не хранить секреты в Claude-диалогах;
- использовать для наблюдения, а не как механизм безопасности.

## 4. Требования

- VS Code `1.105.0+`;
- Claude Code CLI установлен и авторизован;
- проект открыт в VS Code как папка `<PROJECT_ROOT>`.

## 5. Установка через VS Code

Если VS Code установлен:

1. Открыть VS Code.
2. Открыть папку `<PROJECT_ROOT>`.
3. Нажать `Ctrl+P`.
4. Вставить:

```text
ext install pablodelucca.pixel-agents
```

5. Нажать Enter.

## 6. Установка через CLI

Если команда `code` доступна:

```powershell
code --install-extension pablodelucca.pixel-agents
code <PROJECT_ROOT>
```

Если используется portable VS Code, нужно запускать `code.cmd` из его папки:

```powershell
C:\path\to\VSCode\bin\code.cmd --install-extension pablodelucca.pixel-agents
C:\path\to\VSCode\bin\code.cmd <PROJECT_ROOT>
```

## 7. Как пользоваться

1. Открыть проект в VS Code.
2. Открыть нижнюю панель `Pixel Agents`.
3. Нажать `+ Agent`.
4. Расширение создаст Claude Code terminal.
5. Работать с Claude Code в терминале.
6. Наблюдать за персонажем:
   - typing - агент пишет;
   - reading - агент читает файлы;
   - running - агент выполняет команду;
   - waiting - агент ждет пользователя или разрешение.

## 8. Правила для Running Coach

- Не запускать агентов с `--dangerously-skip-permissions`.
- Открывать именно папку `<PROJECT_ROOT>`, чтобы JSONL привязывались к правильному проекту.
- Для каждого крупного направления можно запускать отдельного Claude Code агента:
  - `documentation-agent`;
  - `storage-agent`;
  - `running-data-agent`;
  - `dashboard-agent`;
  - `testing-agent`.
- Не вставлять токены Telegram или LLM API keys в открытый чат агента.
- Секреты хранить только в `.env`, который не должен попадать в git.

## 9. Что не получилось автоматически

Python 3.14.5 установлен успешно.

VS Code в системе изначально не найден. Попытка поставить VS Code user installer не завершилась корректно в текущем окружении. Попытка скачать portable archive была остановлена, потому что повторное скачивание не было разрешено.

Для продолжения автоматической установки нужно разрешить повторную загрузку официального portable VS Code archive или установить VS Code вручную.
