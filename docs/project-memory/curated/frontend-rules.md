# Frontend Rules

## API and state

- Keep all API calls in `frontend/lib/api.ts`.
- API base is selected through `NEXT_PUBLIC_API_BASE_URL`, or falls back to the
  current host with port `8000`.
- Auth/session state and the active shell tab may be persisted client-side for
  continuity, but the backend remains the source of truth for game state.
- Locale is stored through helpers in `frontend/lib/i18n.ts`; API requests send
  `Accept-Language`.
- After claim/repair/auth changes, invalidate relevant TanStack Query data.
- After repair, equip/unequip, destroy, or potion use, also invalidate
  `dungeons` so backend `action_state` is recalculated from current HP,
  equipment, durability, limits, and run state.
- After potion use, invalidate `potions` and `character`; after crafting,
  invalidate `ingredients`, `potions`, and `character`.
- After drag-and-drop equip/unequip on the Character screen, patch relevant
  TanStack Query cache from the server response without fully refetching
  `character`, `inventory`, and `me`; if the mini-inventory drops below 24
  visible pack items and more pages exist, load only the missing items.

## Screens

The main shell `frontend/components/rpg-client.tsx` chooses game screens:

- auth
- create character
- character
- dungeons
- inventory
- leaderboard
- settings

`frontend/components/screens/settings-screen.tsx` exists as a screen and should
be treated as part of the current frontend state. It manages language and the
avatar picker through `api.iconAssets()` / `api.updateAvatar()`.

The create-character screen requires gender selection (`male`/`female`) and
switches class images between `male_media` and `female_media`. The hero portrait
should use `Character.avatar`, while the lower profile avatar in the sidebar
should use `User.avatar` so the profile image is not replaced by hero art.

## UI intent

- The interface should be an actual game UI, not a marketing/landing page.
- The client may format display values, but must not calculate critical game
  formulas, rewards, economy, or server-authoritative results.
- Auto run UI uses the `Auto` button label and the terms "Auto run" /
  "Автозапуск" in guide copy. Only one location can be armed at a time, while
  active server auto state is displayed from the current-run state.
- Dungeon start buttons consume backend `action_state` through the shared
  dungeon-action resolver in `frontend/lib/dungeon-actions.ts`; screens should
  not duplicate blocker/label logic for daily limits, category limits, HP,
  broken gear, current runs, or auto-run summaries.
- Auto-owned current runs hide mini-game and manual claim controls. Stopped
  unread auto-run summaries require explicit acknowledgement before new starts
  are enabled.
- Summary item CTAs open inventory equipment; ingredient CTAs open inventory
  consumables.
- Memory-pairs mini-game: "Accelerate" opens a difficulty selection modal;
  availability, timer, scoring, and run acceleration are server-authoritative.
- Card face art may be resolved through a local catalog/cache for responsiveness,
  but the backend remains the source of truth after admin changes. The board
  should remain locally stable through moves and only update selected/matched
  card state.
- Result modal: green on success with the actual acceleration bonus, red on
  timeout only if the game modal is still open.
- Inventory should show at least 24 cells and load following pages when
  `pagination.has_next` is true.
- Inventory has two sections: equipment and consumables. Consumables combines
  ingredients and potions into stack cells; only potions are clickable/usable.
- Craft panel lives in the consumables section. It fetches backend recipes,
  chooses small/medium/large by `difficulty`, limits batch size by owned
  ingredients, and sends `{recipe_id, quantity}` to the backend.
- Backend returns money as `money_copper`; frontend splits balance into
  gold/silver/copper: `1 gold = 100 silver = 10 000 copper`.
- The power formula tooltip on the Character screen should match backend
  default weights: attack `2`, defense `1.7`, health `0.25`, crit `1`,
  evasion `1`.

## Media sizing

- Frontend media contract contains only `large_url`, `medium_url`, and
  `small_url`; do not use `icon_url`, `thumbnail_url`, or `original_url`.
- `large` is used for dungeon artwork on the dungeons tab, hero portrait, and
  item detail card.
- `medium` is used for equipment slot items, the inventory item list, and
  create-character class cards, choosing the media field for the selected hero
  gender.
- `small` is used for hero mini-inventory, quick dungeon rows, sidebar avatar,
  and leaderboard avatar.
