# Overview

Browser Async RPG MVP - браузерная idle/async RPG: один аккаунт владеет одним
героем, отправляет его в timed dungeon runs, забирает награды, управляет лутом,
экипировкой, прочностью, ремонтом и прогрессией в leaderboard.

## Core Loop

Регистрация -> создание героя -> выбор данжа -> запуск похода -> ожидание ->
claim награды -> опыт/валюта/предмет -> equip/repair/replace -> повтор.

## MVP-границы

- Один аккаунт имеет одного героя.
- Один герой может иметь только один активный `IN_PROGRESS` dungeon run.
- Нет PvP, рынка, крафта, кланов, stamina, party system и real-time combat.
- Сервер считает игровые формулы; клиент не должен считать критичную экономику
  или боевые результаты.
- Django Admin используется как MVP admin/balance CMS.

## Где искать продуктовый смысл

- `README.md` - краткое описание MVP.
- `specs/01_game_design.md` - игровые правила и progression.
- `specs/02_backend_models.md` - модели и связи.
- `specs/03_api_spec.md` - API intent.
- `specs/04_frontend_spec.md` - frontend flow.
- `specs/05_admin_and_balance.md` - admin и balance configs.
- `specs/06_tech_stack.md` - стек и инфраструктура.

