# AGENTS.md

## Project Memory

`docs/project-memory/` — это точка входа в контекст проекта, прошлые решения, архитектурные договоренности и накопленную проектную память.

Project Memory помогает понять намерение, историю и правила проекта, но не является источником истины для текущей реализации.

### Приоритет источников

При работе с проектом используй следующий порядок доверия:

1. Текущий код репозитория
2. Тесты, миграции, схемы, конфиги и runtime-настройки
3. Свежий сгенерированный анализ проекта, например `graphify-out/GRAPH_REPORT.md`
4. Документация проекта
5. `docs/project-memory/`
6. Предыдущие обсуждения и предположения

Если `docs/project-memory/` конфликтует с текущим кодом, доверяй коду.

Если Graphify конфликтует с текущим кодом, доверяй коду.

Если документация конфликтует с текущим кодом, сначала проверь реальную реализацию в репозитории.

### Как использовать Project Memory

Перед любой глубокой работой по этому репозиторию сначала открой:

1. `docs/project-memory/INDEX.md`
2. релевантные файлы из `docs/project-memory/curated/`
3. релевантные файлы из `docs/project-memory/inventories/`

Используй Project Memory для:

- понимания целей проекта
- понимания архитектурных предпочтений
- учета прошлых решений
- соблюдения согласованного стиля работы
- понимания причин, почему были выбраны или отклонены определенные подходы
- сохранения контекста между сессиями

Не используй Project Memory как доказательство:

- точного расположения файлов
- текущих полей моделей
- текущего поведения API
- текущих сигнатур функций
- текущей бизнес-логики
- текущих зависимостей между модулями
- текущей схемы базы данных
- текущего flow фоновых задач
- текущей структуры frontend-компонентов

Все такие детали нужно проверять по реальным файлам репозитория.

### Перед внесением изменений

Для небольших локальных изменений:

1. Изучи целевой файл напрямую.
2. Проверь ближайшие тесты или места использования.
3. Внеси минимальное безопасное изменение.

Для глубокой, архитектурной или межмодульной работы:

1. Открой `docs/project-memory/INDEX.md`.
2. Изучи релевантные файлы из `docs/project-memory/curated/` и `docs/project-memory/inventories/`.
3. Если существует актуальный `graphify-out/GRAPH_REPORT.md`, используй его для понимания структуры и связей.
4. Проверь все важные предположения по текущему коду.
5. Определи затронутые модули, тесты, миграции, конфиги и API-контракты.
6. Сначала объясни план.
7. Затем вноси минимальные безопасные изменения.
8. Запусти или предложи релевантные тесты.

### Работа с устаревшей памятью

Project Memory может быть устаревшей.

Если память говорит одно, а код показывает другое:

- доверяй текущему коду
- кратко укажи на расхождение
- не подгоняй код под память без явной просьбы
- после изменений обнови соответствующие файлы в `docs/project-memory/`

Пример:

> Project Memory указывает, что генерация отчетов находится только в `reports/tasks.py`, но текущий код также использует `reports/services/`. Я буду следовать текущей структуре кода и после изменения обновлю память.

### Что стоит хранить в Project Memory

Хорошие кандидаты для `docs/project-memory/`:

- назначение проекта
- архитектурные принципы
- соглашения по стилю кода
- требования к тестированию
- требования безопасности
- правила именования
- принятые компромиссы
- отклоненные подходы
- продуктовые решения
- особенности окружения, которые редко меняются

Плохие кандидаты:

- точные пути к файлам без необходимости
- точные имена функций
- временные баги
- текущие TODO
- содержимое сгенерированного графа
- детали, которые легко получить из кода
- устаревающие списки всех моделей, endpoint’ов или задач

### Практическое правило

Используй `docs/project-memory/`, чтобы понять намерение.

Используй Graphify, чтобы понять структуру.

Используй код репозитория, чтобы понять реальность.

Если есть сомнения — изучи код.

## Security Rules

- Никогда не открывай, не читай и не анализируй файлы `.env` и `.env.*`.
- Не выполняй команды, которые выводят содержимое `.env` файлов (`cat`, `less`,
  `more`, `grep`, `rg`, `awk`, `sed` и т.д. по этим файлам).
- Если для задачи требуется доступ к секретам, запрашивай у пользователя только
  замаскированные значения, например `API_KEY=***`.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, invoke the `skill` tool with `skill: "graphify"` before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

# Graphify usage

Use graphify-out/GRAPH_REPORT.md only for:
- architecture questions
- impact analysis
- cross-module changes
- onboarding explanations
- refactoring plans

Do not use Graphify for small localized edits where the target file is already known.

Before large changes, first identify related files/modules using Graphify, then inspect source files directly before editing.