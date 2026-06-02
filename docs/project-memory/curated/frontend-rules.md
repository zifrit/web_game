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

## UI intent

- Интерфейс должен быть actual game UI, не marketing/landing page.
- Клиент может форматировать display values, но не должен считать критичные
  игровые формулы, rewards, economy или server-authoritative results.
- Memory-pairs mini-game на Dungeons screen может считать локальные клики/пары,
  но доступность, таймер попытки и ускорение run применяются backend API.
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
  карточек классов при создании персонажа.
- `small` используется для мини-инвентаря героя, quick dungeon rows, sidebar
  avatar и leaderboard avatar.
