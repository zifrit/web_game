# 02. Backend Models Specification

## 1. users

Аккаунт игрока.

```text
id
email
password_hash
money_copper
avatar_media_id nullable
created_at
updated_at
```

## 2. media_assets

Единая таблица медиа-объектов.

```text
id
original_url
large_url
medium_url
small_url
thumbnail_url
icon_url
created_at
updated_at
```

Используется для:

- аватаров пользователя;
- аватаров персонажа;
- предметов;
- данжей;
- UI-изображений.

## 3. character_classes

Шаблон класса героя.

```text
key
name
start_health
start_attack
start_defense
start_critical_chance
start_evasion
growth_profile JSON
media_id nullable
is_active
sort_order
```

## 4. characters

Герой пользователя.

```text
id
user_id
name
class_key
avatar_media_id nullable
level
experience
base_health
base_attack
base_defense
base_critical_chance
base_evasion
power_cached nullable
power_updated_at nullable
created_at
updated_at
```

В MVP:

```text
1 user = 1 character
```

`power_cached` нужен только для будущего leaderboard по power. В MVP leaderboard по power можно не реализовывать.

## 5. dungeon_locations

Локация/данж.

```text
id
name
description
media_id nullable
duration_seconds
required_power
experience_min
experience_max
money_min_copper
money_max_copper
item_drop_chance
rarity_chances JSON
is_active
sort_order
created_at
updated_at
```

## 6. dungeon_runs

Конкретный поход героя.

```text
id
character_id
location_id
status
started_at
ends_at
completed_at nullable
success_chance
is_success nullable
experience_reward nullable
money_reward_copper nullable
items_reward JSON nullable
durability_loss nullable
created_at
updated_at
```

Статусы:

```text
IN_PROGRESS
SUCCESS_WAITING_CLAIM
FAILED_WAITING_CLAIM
CLAIMED
```

Ограничение:

```text
У героя не может быть больше одного IN_PROGRESS run.
```

## 7. dungeon_run_claims

Факт получения награды за поход.

```text
id
dungeon_run_id
user_id
character_id
experience_claimed
money_claimed_copper
created_at
```

Ограничение:

```text
UNIQUE(dungeon_run_id)
```

Это обеспечивает идемпотентность claim.

## 8. dungeon_run_claim_items

Связь между claim и созданными UserItem.

```text
id
claim_id
user_item_id
created_at
```

## 9. item_templates

Шаблон предмета.

```text
id
name
media_id nullable
slot
item_type
allowed_classes JSON nullable
possible_stats JSON
min_durability
max_durability
is_active
created_at
updated_at
```

Пример `possible_stats`:

```json
{
  "attack": { "min": 3, "max": 6 },
  "critical_chance": { "min": 1, "max": 3 },
  "health": { "min": 0, "max": 5 }
}
```

`allowed_classes = null` означает, что предмет универсальный.

## 10. user_items

Конкретный предмет игрока.

```text
id
owner_user_id
source_character_id nullable
equipped_character_id nullable
template_id
name
slot
item_type
rarity
item_level
stats JSON
durability_current
durability_max
created_at
updated_at
```

Пример `stats`:

```json
{
  "attack": 7,
  "critical_chance": 2,
  "health": 10
}
```

## 11. dungeon_location_item_templates

Связующая таблица между локацией и item templates.

```text
id
location_id
item_template_id
created_at
```

Назначение:

```text
Определяет, какие шаблоны предметов могут выпадать в конкретной локации.
```

## 12. rarity_configs

Настройки редкости предметов.

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

## 13. equipment_slot_configs

Справочник слотов экипировки.

```text
key
name
sort_order
is_active
```

Стартовые значения:

```text
weapon
helmet
armor
boots
ring
```

## 14. repair_transactions

История ремонтов.

```text
id
user_id
item_id
cost_copper
durability_before
durability_after
created_at
```

## 15. game_configs

Централизованные игровые коэффициенты и настройки.

```text
key
value JSON
description
updated_at
```

Примеры ключей:

```text
power_formula_config
success_chance_config
rarity_multipliers
item_level_ranges
repair_cost_config
experience_curve_config
stat_caps
```

## 16. Важные ограничения и правила

### Claim идемпотентность

Claim должен проверять наличие `dungeon_run_claims` по `dungeon_run_id`.

Если claim уже есть, повторный запрос не должен начислять награды повторно.

### Экипировка

Один персонаж может иметь только один предмет в одном слоте.

Перед экипировкой нового предмета старый предмет из этого слота снимается.

### Сломанные предметы

```text
durability_current = 0
```

Такой предмет:

- может лежать в сумке;
- может остаться в активном слоте после похода;
- не даёт характеристики;
- блокирует старт нового похода, если находится в активном слоте;
- не может быть надет заново до ремонта.
