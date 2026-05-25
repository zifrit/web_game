# 03. API Specification v0.1

## Общие правила

- API реализуется через Django REST Framework.
- Авторизация через JWT.
- Клиент не рассчитывает игровые формулы.
- Все критичные расчёты делает сервер.
- Все операции claim/repair/equip должны выполняться безопасно и транзакционно там, где это нужно.

---

# 1. Auth API

## POST /auth/register

Регистрация пользователя.

Request:

```json
{
  "email": "user@mail.com",
  "password": "strong_password"
}
```

Response:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "user": {
    "id": 1,
    "email": "user@mail.com",
    "has_character": false
  }
}
```

## POST /auth/login

Request:

```json
{
  "email": "user@mail.com",
  "password": "strong_password"
}
```

Response:

```json
{
  "access_token": "...",
  "refresh_token": "...",
  "user": {
    "id": 1,
    "email": "user@mail.com",
    "has_character": true
  }
}
```

## POST /auth/refresh

Обновление пары токенов.

Должна использоваться refresh token rotation.

## GET /auth/me

Response:

```json
{
  "id": 1,
  "email": "user@mail.com",
  "money_copper": 1250,
  "has_character": true
}
```

## POST /auth/logout

Инвалидирует refresh token.

## JWT requirements

```text
access_token + refresh_token
access token lifetime: 15–30 минут
refresh token lifetime: 7–30 дней
secure signing algorithm
secret/private key через env/secret storage
password hashing через bcrypt/argon2
password_hash никогда не отдаётся в API
```

---

# 2. Character API

## GET /character-classes

Список доступных классов.

Response:

```json
[
  {
    "key": "warrior",
    "name": "Воин",
    "start_stats": {
      "health": 120,
      "attack": 10,
      "defense": 8,
      "critical_chance": 5,
      "evasion": 3
    }
  }
]
```

## POST /characters

Создать героя.

Request:

```json
{
  "name": "Arthas",
  "class_key": "warrior"
}
```

Rules:

```text
1 user = 1 character в MVP
class_key должен существовать и быть active
стартовые статы берутся из character_classes
```

Response:

```json
{
  "id": 1,
  "name": "Arthas",
  "class_key": "warrior",
  "level": 1,
  "experience": 0
}
```

## GET /characters/me

Response:

```json
{
  "id": 1,
  "name": "Arthas",
  "class": {
    "key": "warrior",
    "name": "Воин"
  },
  "level": 1,
  "experience": 0,
  "experience_to_next_level": 100,
  "stats": {
    "health": 120,
    "attack": 10,
    "defense": 8,
    "critical_chance": 5,
    "evasion": 3,
    "power": 68.6
  },
  "equipment": {
    "weapon": null,
    "helmet": null,
    "armor": null,
    "boots": null,
    "ring": null
  }
}
```

---

# 3. Dungeon API

## GET /dungeons

Получить список активных локаций.

Response:

```json
[
  {
    "id": 1,
    "name": "Старый лес",
    "description": "Безопасная стартовая локация.",
    "duration_seconds": 15,
    "required_power": 50,
    "success_chance": 100,
    "item_drop_chance": 10,
    "media": {
      "large_url": "...",
      "medium_url": "...",
      "small_url": "..."
    },
    "rewards_preview": {
      "experience": { "min": 5, "max": 8 },
      "money_copper": { "min": 30, "max": 60 }
    }
  }
]
```

## GET /dungeons/{id}

Детальная информация о локации.

---

# 4. Dungeon Run API

## POST /dungeon-runs

Начать поход.

Request:

```json
{
  "location_id": 1
}
```

Server checks:

```text
1. У пользователя есть герой.
2. У героя нет активного похода.
3. Локация существует и active.
4. В активной экипировке нет предметов с durability_current = 0.
5. Считается power.
6. Считается success_chance.
7. Создаётся DungeonRun со статусом IN_PROGRESS.
```

Response:

```json
{
  "id": 15,
  "status": "IN_PROGRESS",
  "location": {
    "id": 1,
    "name": "Старый лес"
  },
  "started_at": "2026-05-16T10:00:00Z",
  "ends_at": "2026-05-16T10:00:15Z",
  "success_chance": 100
}
```

## GET /dungeon-runs/current

Если поход идёт:

```json
{
  "id": 15,
  "status": "IN_PROGRESS",
  "location": {
    "id": 1,
    "name": "Старый лес"
  },
  "remaining_seconds": 8,
  "ends_at": "2026-05-16T10:00:15Z"
}
```

Если поход завершён, но награда не забрана:

```json
{
  "id": 15,
  "status": "SUCCESS_WAITING_CLAIM",
  "location": {
    "id": 1,
    "name": "Старый лес"
  },
  "result_preview": {
    "is_success": true,
    "experience": 7,
    "money_copper": 42,
    "items_count": 1,
    "durability_loss": 1
  }
}
```

Если активного похода нет:

```json
{
  "current_run": null
}
```

## POST /dungeon-runs/{id}/claim

Claim награды.

Транзакционная логика:

```text
1. Заблокировать dungeon_run.
2. Проверить владельца.
3. Если status = IN_PROGRESS и ends_at <= now — сначала завершить поход.
4. Если claim уже существует — вернуть существующий claim.
5. Если status не SUCCESS_WAITING_CLAIM / FAILED_WAITING_CLAIM — ошибка.
6. Начислить опыт.
7. Проверить level up.
8. Начислить валюту.
9. Создать UserItem из items_reward.
10. Создать DungeonRunClaim.
11. Создать DungeonRunClaimItem для каждого предмета.
12. Списать durability.
13. Перевести run в CLAIMED.
```

Response:

```json
{
  "id": 15,
  "status": "CLAIMED",
  "is_success": true,
  "rewards": {
    "experience": 7,
    "money_copper": 42,
    "items": [
      {
        "id": 100,
        "name": "Обычный ржавый меч",
        "rarity": "common",
        "item_level": 1
      }
    ],
    "durability_loss": 1
  },
  "level_up": {
    "old_level": 1,
    "new_level": 2
  }
}
```

## GET /dungeon-runs/history

Query:

```text
?limit=20
```

Response:

```json
[
  {
    "id": 15,
    "location_name": "Старый лес",
    "status": "CLAIMED",
    "is_success": true,
    "started_at": "...",
    "claimed_at": "..."
  }
]
```

---

# 5. Inventory API

## GET /inventory

Лёгкий список инвентаря.

Response:

```json
{
  "equipment_summary": {
    "health": 25,
    "attack": 12,
    "defense": 8,
    "critical_chance": 3,
    "evasion": 1,
    "power": 34.7
  },
  "equipped": {
    "weapon": {
      "id": 1001,
      "media": {
        "large_url": "...",
        "medium_url": "...",
        "small_url": "..."
      },
      "rarity": "rare",
      "is_broken": false
    },
    "helmet": null,
    "armor": null,
    "boots": null,
    "ring": null
  },
  "items": [
    {
      "id": 1002,
      "media": {
        "large_url": "...",
        "medium_url": "...",
        "small_url": "..."
      },
      "rarity": "common",
      "is_broken": true
    }
  ]
}
```

`equipment_summary` — сумма бонусов только от экипировки.

## GET /inventory/items/{item_id}

Детали предмета.

Response:

```json
{
  "id": 1001,
  "name": "Редкий ржавый меч",
  "slot": "weapon",
  "item_type": "sword",
  "rarity": "rare",
  "item_level": 4,
  "stats": {
    "attack": 7,
    "critical_chance": 2
  },
  "durability": {
    "current": 12,
    "max": 24
  },
  "is_equipped": true,
  "is_broken": false,
  "can_equip": true,
  "media": {
    "large_url": "...",
    "medium_url": "...",
    "small_url": "..."
  }
}
```

## GET /inventory/items/{item_id}/repair-preview

Расчёт стоимости ремонта без изменения данных.

Response:

```json
{
  "item_id": 1001,
  "durability": {
    "current": 12,
    "max": 24,
    "missing": 12
  },
  "repair_cost_copper": 120,
  "user_money_copper": 540,
  "can_repair": true
}
```

## POST /inventory/items/{item_id}/repair

Ремонт предмета.

Важно: сервер заново рассчитывает стоимость, не доверяя preview.

Response:

```json
{
  "success": true,
  "repair_cost_copper": 120,
  "durability": {
    "current": 24,
    "max": 24
  },
  "remaining_money_copper": 420
}
```

## POST /inventory/items/{item_id}/equip

Экипировать предмет.

Checks:

```text
1. Предмет принадлежит пользователю.
2. Предмет не сломан.
3. Класс героя подходит.
4. Слот валиден.
5. Если в слоте уже есть предмет — старый снимается.
```

Response:

```json
{
  "success": true,
  "equipped_slot": "weapon",
  "item_id": 1001,
  "new_power": 84.2
}
```

## POST /inventory/items/{item_id}/unequip

Снять предмет.

Response:

```json
{
  "success": true,
  "new_power": 76.5
}
```

---

# 6. Leaderboard API

MVP только рейтинг по уровню.

## GET /leaderboard?type=level

Response:

```json
{
  "type": "level",
  "items": [
    {
      "rank": 1,
      "character_id": 12,
      "character_name": "Arthas",
      "class": {
        "key": "warrior",
        "name": "Воин"
      },
      "level": 8,
      "avatar": {
        "large_url": "...",
        "medium_url": "...",
        "small_url": "..."
      }
    }
  ],
  "my_rank": {
    "rank": 153,
    "character_id": 1,
    "level": 3
  }
}
```

Leaderboard по power откладывается на будущую версию.
