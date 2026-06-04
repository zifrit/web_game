# Frontend Inventory

Updated from code inspection on 2026-05-30.

## Entrypoints

- `frontend/app/layout.tsx` - root layout, fonts, metadata.
- `frontend/app/page.tsx` - renders the main app.
- `frontend/app/globals.css` - global styling.
- `frontend/components/rpg-client.tsx` - main client shell, nav, screen routing.
  It persists selected tab in `localStorage` key `activeTab`.

## Providers and shared UI

- `frontend/components/providers.tsx` - session provider, locale provider,
  app providers.
- `frontend/components/query-provider.tsx` - TanStack Query provider.
- `frontend/components/ui.tsx` - shared UI primitives and format helpers.

## Screens

- `frontend/components/screens/auth-screen.tsx`
- `frontend/components/screens/create-character-screen.tsx`
- `frontend/components/screens/character-screen.tsx`
- `frontend/components/screens/dungeons-screen.tsx`
- `frontend/components/screens/inventory-screen.tsx`
- `frontend/components/screens/leaderboard-screen.tsx`
- `frontend/components/screens/settings-screen.tsx`

## Libraries

- `frontend/lib/api.ts` - API client, token storage, refresh flow, facade.
- `frontend/lib/types.ts` - API/domain TypeScript types.
- `frontend/lib/i18n.ts` - locale dictionaries, formatting, storage.
- `frontend/lib/media.ts` - media URL selection helper for `large_url`,
  `medium_url`, `small_url`.
- `frontend/lib/i18n.ts` also owns copper splitting/formatting helpers for
  topbar money display.

## Media usage

- Large: dungeons screen artwork, character portrait, item detail artwork.
- Medium: equipment slots, inventory item list, create-character class cards.
- Small: character mini-inventory, quick dungeon rows, sidebar avatar,
  leaderboard avatar.

Create-character class cards choose `male_media` or `female_media` from
`GET /api/character-classes` based on the selected gender and submit that
gender through `api.createCharacter()`.

## Settings and avatar

- Settings screen fetches current user/character and lists icon assets only when
  avatar picker opens.
- Avatar save calls `PATCH /api/auth/me/avatar` via `api.updateAvatar()` and
  patches the `me` TanStack Query cache.
- Settings screen includes a Security card for TOTP. Enable starts setup,
  displays QR/manual key and requires a 6-digit confirmation code; disable
  requires current password and current TOTP code.
- Auth screen handles two-step login: `api.login()` may return
  `two_factor_required` and a `challenge_token`; `api.verifyLoginTotp()` then
  returns normal auth tokens.

## API facade methods

- `register`, `login`, `verifyLoginTotp`, `logout`, `me`
- `twoFactorStatus`, `startTwoFactorSetup`, `confirmTwoFactorSetup`,
  `disableTwoFactor`
- `characterClasses`, `createCharacter`, `character`
- `dungeons`, `startRun`, `currentRun`, `claimRun`
- `startMiniGame` (config_id), `revealMiniGameCard`, `moveMiniGame`,
  `miniGameConfigs`, `miniGameCardFaces`, `miniGameHistory`
  (SVG-каталог кешируется хуком `useCardFaces` в localStorage по версии)
- `inventory`, `item`, `repairPreview`, `repair`, `destroyPreview`,
  `destroy`, `equip`, `unequip`
- `leaderboard`
- `iconAssets`, `updateAvatar`

Inventory screen notes:

- Top inventory action enters multi-select mode instead of repairing all.
- Repair and destroy use bulk API calls; detail panel sends a single selected
  item id to the same bulk endpoints.

## Package scripts

- `npm run dev`
- `npm run build`
- `npm run start`
- `npm run lint`
