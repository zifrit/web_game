# 05. Admin and Balance Specification

## 1. Главная идея

Django Admin используется как внутренняя игровая CMS.

Через админку управляются:

- классы;
- данжи;
- шаблоны предметов;
- редкости;
- слоты экипировки;
- формулы/коэффициенты;
- медиа;
- история походов;
- история claim;
- история ремонтов.

Не нужно делать отдельную admin frontend panel в MVP.

## 2. Admin sections

### 2.1 Character Classes

Управление:

```text
key
name
start stats
growth_profile
media
is_active
sort_order
```

Важно удобно редактировать `growth_profile JSON`.

### 2.2 Dungeon Locations

Управление:

```text
name
description
media
duration_seconds
required_power
experience_min/max
money_min/max
item_drop_chance
rarity_chances
is_active
sort_order
```

Inline:

```text
DungeonLocationItemTemplate
```

Чтобы прямо на странице данжа выбирать возможные item templates.

### 2.3 Item Templates

Управление:

```text
name
media
slot
item_type
allowed_classes
possible_stats
min_durability
max_durability
is_active
```

### 2.4 Rarity Configs

Управление:

```text
key
name
stat_multiplier
min_item_level
max_item_level
min_stats_count
max_stats_count
sort_order
is_active
```

### 2.5 Equipment Slot Configs

Управление:

```text
key
name
sort_order
is_active
```

### 2.6 Game Configs

Центральная таблица коэффициентов:

```text
power_formula_config
success_chance_config
repair_cost_config
experience_curve_config
stat_caps
```

Все игровые коэффициенты должны меняться без деплоя.

### 2.7 Media Assets

Управление:

```text
name
asset_type
original
large
medium
small
```

### 2.8 Dungeon Runs

Read-only/mostly read-only просмотр:

```text
character
location
status
started_at
ends_at
completed_at
success_chance
is_success
experience_reward
money_reward_copper
items_reward
durability_loss
```

### 2.9 Dungeon Run Claims

Просмотр факта получения награды:

```text
dungeon_run
user
character
experience_claimed
money_claimed_copper
created_at
claim items
```

### 2.10 User Items

Просмотр и отладка предметов:

```text
owner
source_character
equipped_character
template
name
slot
item_type
rarity
item_level
stats
durability_current
durability_max
```

### 2.11 Repair Transactions

Просмотр экономики ремонта:

```text
user
item
cost_copper
durability_before
durability_after
created_at
```

## 3. Balance page / internal view

На MVP можно начать с Django Admin.

Позже можно добавить read-only страницу:

```text
/admin/balance-overview
```

Где видно:

- power formula;
- success chance formula;
- rarity multipliers;
- item level ranges;
- stat caps;
- стартовые данжи;
- стартовые классы.

## 4. Важные требования

### Формулы централизованы

Формулы не должны быть размазаны по serializer/view/model.

Использовать сервисный слой:

```text
GameFormulaService
GameBalanceService
LootGenerationService
DungeonRunService
InventoryService
```

### Конфиги из БД

Коэффициенты должны подтягиваться из `game_configs` или профильных таблиц.

### Админка не должна ломать игру

Нужна валидация:

- сумма rarity_chances должна быть 100;
- min не должен быть больше max;
- item_level ranges не должны быть невалидными;
- item_drop_chance в пределах 0–100;
- success chance caps в пределах 0–100;
- active dungeon должен иметь хотя бы один возможный item_template, если item_drop_chance > 0.
