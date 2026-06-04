# Frontend Rules

## API and state

- Все API вызовы держать через `frontend/lib/api.ts`.
- API base выбирается через `NEXT_PUBLIC_API_BASE_URL` или fallback на текущий
  host с портом `8000`.
- Tokens хранятся в `localStorage` ключом `rpg_tokens`.
- Активная вкладка shell хранится в `localStorage` ключом `activeTab`.
- Locale хранится через helpers в `frontend/lib/i18n.ts`; API получает
  `Accept-Language`.
- После claim/repair/auth changes инвалидировать relevant TanStack Query data.
- После drag-and-drop equip/unequip на Character screen патчить relevant
  TanStack Query cache из server response без полной перезагрузки
  `character`, `inventory` и `me`; если мини-инвентарь просел ниже 24 видимых
  pack-предметов и есть следующие страницы, дозагрузить только недостающие
  предметы.

## Screens

Главный shell `frontend/components/rpg-client.tsx` выбирает игровые экраны:

- auth
- create character
- character
- dungeons
- inventory
- leaderboard
- settings

`frontend/components/screens/settings-screen.tsx` существует как экран и должен
считаться частью текущего frontend-состояния. Он управляет языком и avatar
picker через `api.iconAssets()` / `api.updateAvatar()`.

Create-character screen требует выбор пола (`male`/`female`) и переключает
картинки классов между `male_media` и `female_media`; после создания shell
должен предпочитать `Character.avatar` перед `User.avatar`.

## UI intent

- Интерфейс должен быть actual game UI, не marketing/landing page.
- Клиент может форматировать display values, но не должен считать критичные
  игровые формулы, rewards, economy или server-authoritative results.
- Memory-pairs mini-game: «Ускорить» открывает модалку выбора сложности
  (проценты из `GET /mini-game/configs`), выбор шлёт `config_id` в start;
  доступность, таймер, подсчёт и ускорение run — server-authoritative.
- Доска приходит по `code`; SVG-лица резолвятся локально из каталога
  `GET /mini-game/card-faces` (хук `useCardFaces`, кеш в localStorage по версии,
  фоллбэк на статику `public/memory-faces/`). `reveal`/`move` возвращают флаг
  `finished`; при `finished` показать result-модалку.
- Result-модалка: зелёная при SUCCESS с фактическим `duration_reduction_seconds`,
  красная при таймауте только если игровая модалка ещё открыта. Доска должна
  оставаться локально стабильной: не заменять весь board после хода, обновлять
  только выбранные/совпавшие карточки.
- Inventory должен показывать минимум 24 cells и догружать следующие страницы,
  если `pagination.has_next` true.
- Backend возвращает деньги в `money_copper`; frontend разбивает баланс на
  золото/серебро/медь: `1 gold = 100 silver = 10 000 copper`.
- Tooltip формулы мощи на Character screen должен соответствовать backend
  default weights: attack `2`, defense `1.7`, health `0.25`, crit `1`,
  evasion `1`.

## Media sizing

- Frontend media contract содержит только `large_url`, `medium_url`,
  `small_url`; не использовать `icon_url`, `thumbnail_url`, `original_url`.
- `large` используется для dungeon artwork на вкладке dungeons, портрета героя
  и детальной карточки предмета.
- `medium` используется для предметов в equipment slots, списка inventory и
  карточек классов при создании персонажа, выбирая поле медиа по выбранному
  полу героя.
- `small` используется для мини-инвентаря героя, quick dungeon rows, sidebar
  avatar и leaderboard avatar.
