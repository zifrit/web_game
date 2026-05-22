# Frontend Rules

## API and state

- Все API вызовы держать через `frontend/lib/api.ts`.
- API base выбирается через `NEXT_PUBLIC_API_BASE_URL` или fallback на текущий
  host с портом `8000`.
- Tokens хранятся в `localStorage` ключом `rpg_tokens`.
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
считаться частью текущего frontend-состояния, если код его содержит.

## UI intent

- Интерфейс должен быть actual game UI, не marketing/landing page.
- Клиент может форматировать display values, но не должен считать критичные
  игровые формулы, rewards, economy или server-authoritative results.
- Inventory должен показывать минимум 24 cells и догружать следующие страницы,
  если `pagination.has_next` true.
