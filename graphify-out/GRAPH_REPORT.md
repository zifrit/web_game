# Graph Report - .  (2026-05-31)

## Corpus Check
- Corpus is ~46,526 words - fits in a single context window. You may not need a graph.

## Summary
- 887 nodes · 1829 edges · 70 communities (43 shown, 27 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 299 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Domain Models|Domain Models]]
- [[_COMMUNITY_Game Services|Game Services]]
- [[_COMMUNITY_API Views|API Views]]
- [[_COMMUNITY_Domain Models|Domain Models]]
- [[_COMMUNITY_Domain Models|Domain Models]]
- [[_COMMUNITY_Dungeon Runs|Dungeon Runs]]
- [[_COMMUNITY_Frontend Shell|Frontend Shell]]
- [[_COMMUNITY_Dungeon Runs|Dungeon Runs]]
- [[_COMMUNITY_Frontend Dependencies|Frontend Dependencies]]
- [[_COMMUNITY_Domain Models|Domain Models]]
- [[_COMMUNITY_Frontend Providers|Frontend Providers]]
- [[_COMMUNITY_TOTP Backend|TOTP Backend]]
- [[_COMMUNITY_Domain Models|Domain Models]]
- [[_COMMUNITY_Frontend Providers|Frontend Providers]]
- [[_COMMUNITY_Dungeon Runs|Dungeon Runs]]
- [[_COMMUNITY_TypeScript Config|TypeScript Config]]
- [[_COMMUNITY_Domain Models|Domain Models]]
- [[_COMMUNITY_Domain Models|Domain Models]]
- [[_COMMUNITY_Seed Commands|Seed Commands]]
- [[_COMMUNITY_Dungeon Runs|Dungeon Runs]]
- [[_COMMUNITY_Auth And 2FA|Auth And 2FA]]
- [[_COMMUNITY_Seed Commands|Seed Commands]]
- [[_COMMUNITY_Test Suite|Test Suite]]
- [[_COMMUNITY_Project Memory|Project Memory]]
- [[_COMMUNITY_Dungeon Runs|Dungeon Runs]]
- [[_COMMUNITY_Docker Runtime|Docker Runtime]]
- [[_COMMUNITY_Seed Commands|Seed Commands]]
- [[_COMMUNITY_Inventory UI|Inventory UI]]
- [[_COMMUNITY_Project Module|Project Module]]
- [[_COMMUNITY_Frontend Providers|Frontend Providers]]
- [[_COMMUNITY_Django Admin|Django Admin]]
- [[_COMMUNITY_Media Assets|Media Assets]]
- [[_COMMUNITY_Domain Models|Domain Models]]
- [[_COMMUNITY_Django Migrations|Django Migrations]]
- [[_COMMUNITY_Django Migrations|Django Migrations]]
- [[_COMMUNITY_Django Migrations|Django Migrations]]
- [[_COMMUNITY_Django Migrations|Django Migrations]]
- [[_COMMUNITY_Media Assets|Media Assets]]
- [[_COMMUNITY_Media Assets|Media Assets]]
- [[_COMMUNITY_Ranks And Rarity|Ranks And Rarity]]
- [[_COMMUNITY_Frontend Dependencies|Frontend Dependencies]]
- [[_COMMUNITY_Ranks And Rarity|Ranks And Rarity]]
- [[_COMMUNITY_UI System|UI System]]
- [[_COMMUNITY_Frontend Providers|Frontend Providers]]
- [[_COMMUNITY_Domain Models|Domain Models]]
- [[_COMMUNITY_Domain Models|Domain Models]]
- [[_COMMUNITY_Auth And 2FA|Auth And 2FA]]
- [[_COMMUNITY_Frontend Providers|Frontend Providers]]
- [[_COMMUNITY_Frontend Providers|Frontend Providers]]
- [[_COMMUNITY_Django Admin|Django Admin]]
- [[_COMMUNITY_Frontend Dependencies|Frontend Dependencies]]
- [[_COMMUNITY_Frontend Dependencies|Frontend Dependencies]]
- [[_COMMUNITY_Game Services|Game Services]]
- [[_COMMUNITY_Frontend Dependencies|Frontend Dependencies]]
- [[_COMMUNITY_TypeScript Config|TypeScript Config]]

## God Nodes (most connected - your core abstractions)
1. `MediaAsset` - 37 edges
2. `TimestampedModel` - 36 edges
3. `GameFormulaService` - 35 edges
4. `InventoryService` - 33 edges
5. `User` - 29 edges
6. `useI18n()` - 24 edges
7. `RankedSeedTests` - 24 edges
8. `Character` - 24 edges
9. `message()` - 22 edges
10. `DungeonRunService` - 21 edges

## Surprising Connections (you probably didn't know these)
- `Initial User Character Dungeon Inventory Models` --implements--> `Async RPG Core Loop`  [INFERRED]
  backend/apps/game/migrations/0001_initial.py → README.md
- `Async RPG Core Loop` --conceptually_related_to--> `Dungeon Run Service`  [INFERRED]
  README.md → backend/apps/game/services.py
- `Async RPG Core Loop` --conceptually_related_to--> `Inventory Service`  [INFERRED]
  README.md → backend/apps/game/services.py
- `MVP Gameplay Constraints` --rationale_for--> `Dungeon Run Service`  [INFERRED]
  README.md → backend/apps/game/services.py
- `Django Manage Entrypoint` --implements--> `Django Backend Service`  [EXTRACTED]
  backend/manage.py → docker-compose.yml

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Media contract migrated to FileField variants and serialized as public resized URLs** — backend.apps.game.models.MediaAsset, backend.apps.game.serializers.common.media_payload, migration.0006.mediaasset_asset_type_resize_contract [EXTRACTED 0.94]
- **Dungeon loot now uses location item_drop_chance plus per-template chance weights and template rank** — backend.apps.game.models.DungeonLocation, backend.apps.game.models.DungeonLocationItemTemplate, backend.apps.game.models.ItemTemplate, migration.0008.itemtemplate_rarity_key, migration.0009.location_item_template_chance [EXTRACTED 0.95]
- **Inventory serializers render UserItem state, localization, media payload, equipment, durability, and unlimited-capacity pagination** — backend.apps.game.models.UserItem, backend.apps.game.serializers.common.localized_item_name, backend.apps.game.serializers.common.media_payload, backend.apps.game.serializers.inventory.UserItemSummarySerializer, backend.apps.game.serializers.inventory.UserItemDetailSerializer, backend.apps.game.serializers.inventory.InventorySerializer [EXTRACTED 0.92]
- **TOTP account protection spans persistent UserTwoFactor state, migration creation, and auth token response exposure** — backend.apps.game.models.User, backend.apps.game.models.UserTwoFactor, backend.apps.game.serializers.auth.token_response, migration.0010.usertwofactor [EXTRACTED 0.90]
- **TOTP setup, confirmation, login, and disable lifecycle** — game.views.auth.totp_views, docs.totp_flow, tests.mvp_api, concept.totp_lifecycle [EXTRACTED 0.97]
- **Dungeon run preview, start, current/finalize, claim, and history lifecycle** — game.views.dungeons.location_views, game.views.dungeons.run_views, docs.dungeon_run_flow, tests.mvp_api, tests.services.formulas_and_lifecycle, concept.dungeon_claim_idempotency [EXTRACTED 0.97]
- **Inventory read and mutation API surface** — game.views.inventory.read_views, game.views.inventory.mutation_views, tests.mvp_api, tests.services.inventory_and_seed, concept.inventory_bulk_mutations [EXTRACTED 0.95]
- **Django runtime and worker configuration** — config.runtime, config.entrypoints, memory.architecture, docs.dungeon_run_flow [EXTRACTED 0.93]
- **Frontend shell composition** — code:home-page, code:app-providers, code:rpg-client, code:sidebar, code:mobile-nav, code:topbar [EXTRACTED 0.97]
- **State, locale, token, and API contract** — concept:frontend-state-contract, code:session-provider, code:locale-provider, code:rpg-client, concept:api-domains [EXTRACTED 0.94]
- **Runtime and verification loop** — doc:runtime-and-config, doc:local-run, doc:verification, concept:runtime-stack, concept:verification-strategy [EXTRACTED 0.93]
- **Security and generated-file hygiene** — doc:gotchas, doc:working-rules, concept:security-no-env, code:next-env [EXTRACTED 0.95]
- **Shared frontend UI system** — code:tailwind-config, code:ui-primitives, code:item-glyph, code:skeleton-screens, concept:media-contract [INFERRED 0.89]
- **Frontend player flow implementation** — code:AuthScreen, code:CreateCharacterScreen, code:CharacterScreen, code:DungeonsScreen, code:InventoryScreen, code:LeaderboardScreen, concept:PlayerFlow [EXTRACTED 0.90]
- **Inventory and equipment cache consistency** — code:CharacterScreen, code:CharacterScreen:inventory-cache-merge, code:InventoryScreen, code:InventoryScreen:ItemDetailPanel, concept:InventoryApi, concept:EquipmentSlots [EXTRACTED 0.93]
- **Dungeon run and claim loop** — code:DungeonsScreen, code:DungeonsScreen:ActiveRunBanner, code:CharacterScreen:ActiveExpeditionStrip, concept:DungeonRunApi, concept:DungeonRunStatus, concept:ClaimIdempotency [EXTRACTED 0.92]
- **Media usage contract across screens** — code:bestMediaUrl, code:CreateCharacterScreen, code:CharacterScreen, code:DungeonsScreen, code:InventoryScreen, code:LeaderboardScreen, code:SettingsScreen, concept:MediaAssetContract [EXTRACTED 0.94]
- **Server-authoritative gameplay boundary** — concept:ServerAuthoritativeRules, concept:CentralizedGameConfig, concept:PowerFormula, concept:SuccessChanceFormula, concept:RepairFlow, code:api-facade, code:types [EXTRACTED 0.89]

## Communities (70 total, 27 thin omitted)

### Community 0 - "Domain Models"
Cohesion: 0.06
Nodes (57): AbstractBaseUser, AutocompleteSelect, str, str, str, str, bool, str (+49 more)

### Community 1 - "Game Services"
Cohesion: 0.05
Nodes (31): str, UserItem, GameBalanceService, GameFormulaService, LoginSerializer, RegisterSerializer, token_response(), TotpCodeSerializer (+23 more)

### Community 2 - "API Views"
Cohesion: 0.08
Nodes (41): APIView, str, int, int, request_locale(), resolve_locale(), translate(), DungeonRunService (+33 more)

### Community 3 - "Domain Models"
Cohesion: 0.10
Nodes (20): Any, bool, int, ItemTemplate, str, UserItem, Character, CharacterClass (+12 more)

### Community 4 - "Domain Models"
Cohesion: 0.05
Nodes (48): Initial User Character Dungeon Inventory Models, Initial Game Schema Migration, Unique In Progress Run Constraint, I18n Fields Migration, Inventory and Repair Admins, User Two Factor Admin, Project Memory Rules, Security Rules (+40 more)

### Community 5 - "Dungeon Runs"
Cohesion: 0.07
Nodes (47): AuthScreen, CharacterScreen, ActiveExpeditionStrip, PowerHelp, CharacterScreen inventory cache merge, CreateCharacterScreen, DungeonsScreen, ActiveRunBanner (+39 more)

### Community 6 - "Frontend Shell"
Cohesion: 0.10
Nodes (25): AppProviders(), useI18n(), ADVENTURE_NAV, HERO_NAV, MobileNav(), PAGE_META, RpgClient(), Sidebar() (+17 more)

### Community 7 - "Dungeon Runs"
Cohesion: 0.08
Nodes (27): Character, ClaimResponse, CurrentRunResponse, DestroyPreview, DestroyResponse, Dungeon, DungeonRunStatus, EquipmentSlot (+19 more)

### Community 8 - "Frontend Dependencies"
Cohesion: 0.07
Nodes (29): dependencies, clsx, @hookform/resolvers, lucide-react, next, react, react-dom, react-hook-form (+21 more)

### Community 9 - "Domain Models"
Cohesion: 0.11
Nodes (28): Character is the single account hero with class, avatar, progress, base stats, and cached power, CharacterClass defines base stats, growth profile, media, and active ordering, DungeonLocation defines duration, required power, reward ranges, item_drop_chance, media, and active ordering, DungeonLocationItemTemplate links locations to item templates with chance weights and uniqueness, DungeonRun records one timed dungeon attempt, status, success chance, rewards, durability loss, and unique active-run constraint, DungeonRunClaim is a one-to-one idempotency record for claimed dungeon rewards, DungeonRunClaimItem links a claim to awarded UserItem rows, ItemTemplate defines seedable loot template, slot/type, rarity_key, allowed classes, stats, durability, and media (+20 more)

### Community 10 - "Frontend Providers"
Cohesion: 0.10
Nodes (27): AppProviders, Frontend Package Manifest, Home Page, ItemGlyph, LocaleProvider, MobileNav, Next Config, PostCSS Config (+19 more)

### Community 11 - "TOTP Backend"
Cohesion: 0.17
Nodes (20): bool, int, str, create_login_challenge(), create_totp_secret(), current_timecode(), decrypt_secret(), encrypt_secret() (+12 more)

### Community 12 - "Domain Models"
Cohesion: 0.12
Nodes (22): SessionProvider(), apiBase(), ApiError, apiFetch(), ApiUser, AuthPayload, Character, CharacterClass (+14 more)

### Community 13 - "Frontend Providers"
Cohesion: 0.12
Nodes (18): LocaleContext, LocaleContextValue, queryClient, SessionContext, SessionContextValue, setApiLocale(), Locale, makeTranslator() (+10 more)

### Community 14 - "Dungeon Runs"
Cohesion: 0.12
Nodes (22): Dungeon claim idempotency, Inventory bulk mutation pattern, Media payload contract, TOTP lifecycle, Django and Celery entrypoints, Django runtime configuration, Dungeon Run Flow, TOTP Flow And API Calls (+14 more)

### Community 15 - "TypeScript Config"
Cohesion: 0.10
Nodes (19): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+11 more)

### Community 16 - "Domain Models"
Cohesion: 0.11
Nodes (5): CharacterScreenSkeleton(), InventoryScreenSkeleton(), rarityBorder, rarityText, Skeleton()

### Community 17 - "Domain Models"
Cohesion: 0.15
Nodes (12): InventoryMutationResponse, addUniqueItem(), DragState, EQUIPMENT_SLOTS, InvCell(), mergeInventoryMutation(), POWER_WEIGHTS, RARITY_COLOR (+4 more)

### Community 19 - "Dungeon Runs"
Cohesion: 0.15
Nodes (4): TestCase, ApiSmokeTests, DungeonLifecycleTests, GameFormulaTests

### Community 20 - "Auth And 2FA"
Cohesion: 0.21
Nodes (12): useSession(), ErrorNotice(), api, formatStatName(), CharacterClass, AuthMode, authSchema(), AuthScreen() (+4 more)

### Community 21 - "Seed Commands"
Cohesion: 0.21
Nodes (10): int, bool, int, ItemTemplate, rank_for_level(), RankConfig, _durability_for_rank(), EquipmentKind (+2 more)

### Community 23 - "Project Memory"
Cohesion: 0.22
Nodes (9): Next Type Declarations, Runtime Stack, No .env Inspection Rule, Verification Strategy, Project Gotchas, Local Run Inventory, Runtime And Config Inventory, Verification Inventory (+1 more)

### Community 24 - "Dungeon Runs"
Cohesion: 0.32
Nodes (6): formatDuration(), DungeonRun, ActiveRunBanner(), formatTime(), TIER_GRADIENT, useRemainingSeconds()

### Community 25 - "Docker Runtime"
Cohesion: 0.48
Nodes (7): Django Backend Service, Celery Worker and Beat Services, Docker Compose Runtime Stack, Next Frontend Service, PostgreSQL Service, Redis Service, Django Manage Entrypoint

### Community 26 - "Seed Commands"
Cohesion: 0.29
Nodes (3): BaseCommand, Command, Command

### Community 28 - "Project Module"
Cohesion: 0.33
Nodes (4): cinzel, inter, jetbrainsMono, metadata

### Community 30 - "Django Admin"
Cohesion: 0.67
Nodes (3): Cached Selected Autocomplete Select, Dungeon Admins, Dungeon Location Item Template Inline

### Community 31 - "Media Assets"
Cohesion: 0.67
Nodes (3): Media Asset Admin, Game Image Mini Specification, MediaAsset Image Sizes

## Knowledge Gaps
- **182 isolated node(s):** `config`, `config`, `name`, `version`, `private` (+177 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `GameFormulaService` connect `Game Services` to `Domain Models`, `API Views`, `Domain Models`, `Seed Commands`, `Dungeon Runs`, `Inventory UI`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `message()` connect `Domain Models` to `Domain Models`, `Game Services`, `API Views`, `TOTP Backend`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `InventoryService` connect `Domain Models` to `Domain Models`, `Game Services`, `API Views`, `Seed Commands`, `Dungeon Runs`, `Inventory UI`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 23 inferred relationships involving `MediaAsset` (e.g. with `str` and `str`) actually correct?**
  _`MediaAsset` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `TimestampedModel` (e.g. with `str` and `str`) actually correct?**
  _`TimestampedModel` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 26 inferred relationships involving `GameFormulaService` (e.g. with `CharacterClassSerializer` and `CharacterCreateSerializer`) actually correct?**
  _`GameFormulaService` has 26 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `InventoryService` (e.g. with `int` and `InventorySerializer`) actually correct?**
  _`InventoryService` has 20 INFERRED edges - model-reasoned connections that need verification._