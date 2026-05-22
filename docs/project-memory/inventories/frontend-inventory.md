# Frontend Inventory

Updated from code inspection on 2026-05-22.

## Entrypoints

- `frontend/app/layout.tsx` - root layout, fonts, metadata.
- `frontend/app/page.tsx` - renders the main app.
- `frontend/app/globals.css` - global styling.
- `frontend/components/rpg-client.tsx` - main client shell, nav, screen routing.

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
- `frontend/lib/media.ts` - media URL selection helper.

## API facade methods

- `register`, `login`, `logout`, `me`
- `characterClasses`, `createCharacter`, `character`
- `dungeons`, `startRun`, `currentRun`, `claimRun`
- `inventory`, `item`, `repairPreview`, `repair`, `equip`, `unequip`
- `leaderboard`

## Package scripts

- `npm run dev`
- `npm run build`
- `npm run start`
- `npm run lint`

