# Overview

Browser Async RPG MVP is a browser-based idle/async RPG: one account owns one
hero, sends that hero on timed dungeon runs, claims rewards, and manages loot,
equipment, durability, repairs, potion crafting, and leaderboard progression.

## Core Loop

Register -> create hero -> choose dungeon -> start run -> wait -> claim rewards
-> experience/currency/item/ingredients -> equip/repair/replace and/or brew
potions -> repeat.

## MVP Scope

- One account has one hero.
- One hero can have only one active `IN_PROGRESS` dungeon run.
- Potion crafting exists as a limited MVP loop: ingredients drop from dungeons,
  and recipes brew healing potions in batches. There is no PvP, market,
  equipment item crafting, clans, stamina, party system, or real-time combat.
- The server calculates game formulas; the client must not calculate critical
  economy or combat results.
- Django Admin is used as the MVP admin/balance CMS.

## Where To Find Product Intent

- `README.md` - short MVP description.
- `specs/01_game_design.md` - game rules and progression.
- `specs/02_backend_models.md` - models and relationships.
- `specs/03_api_spec.md` - API intent.
- `specs/04_frontend_spec.md` - frontend flow.
- `specs/05_admin_and_balance.md` - admin and balance configs.
- `specs/06_tech_stack.md` - stack and infrastructure.
