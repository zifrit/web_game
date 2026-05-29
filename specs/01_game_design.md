# 01. Game Design Specification

## 1. Игровая модель

Игрок создаёт аккаунт, затем одного героя. Герой отправляется в данжи, которые имеют длительность, требуемый power, шанс дропа предмета, награды по опыту и валюте.

После завершения похода игрок вручную нажимает `Claim Reward`, чтобы получить результат.

## 2. Классы MVP

Доступные классы:

| Класс | key | HP | Attack | Defense | Crit | Evasion |
|---|---|---:|---:|---:|---:|---:|
| Воин | warrior | 120 | 10 | 8 | 5% | 3% |
| Маг | mage | 80 | 16 | 3 | 8% | 4% |
| Лучник | archer | 95 | 12 | 5 | 12% | 8% |
| Ассассин | assassin | 75 | 14 | 3 | 20% | 15% |

## 3. Характеристики героя

```text
level
experience
health
attack
defense
critical_chance
evasion
power
```

`power` не хранится как основное значение. Он рассчитывается динамически на основе статов героя и экипировки.

## 4. Power formula

```text
power = attack * 2 + defense * 1.7 + health * 0.25 + critical_chance * 1.0 + evasion * 1.0
```

Power считается с учётом:

```text
base_stats + level_growth + active_equipment_stats - broken_equipment_stats
```

Сломанная экипировка остаётся в слоте, но не даёт характеристики.

## 5. Success chance formula

```text
success_chance = 75 + (character_power - location_required_power) * 1.5
```

Ограничения:

```text
min_success_chance = 35%
max_success_chance = 100%
```

## 6. Стартовые локации

| Локация | Время | Required Power | Item Drop Chance | Роль |
|---|---:|---:|---:|---|
| Старый лес | 15 секунд | 50 | 10% | безопасный старт |
| Заброшенная тропа | 30 секунд | 70 | 15% | лёгкий риск / быстрый фарм |
| Сырая пещера | 5 минут | 100 | 25% | рискованный early dungeon |

## 7. Статусы похода

```text
IN_PROGRESS
SUCCESS_WAITING_CLAIM
FAILED_WAITING_CLAIM
CLAIMED
```

## 8. Прочность экипировки

Каждый экипируемый предмет имеет:

```text
durability_current
durability_max
```

Потеря прочности в MVP:

```text
успех: -1 durability
провал: -5 durability
```

Правила сломанной экипировки:

1. Если предмет сломался после похода, он остаётся в активном слоте.
2. Сломанный предмет не даёт характеристики.
3. Сломанный предмет блокирует старт нового похода.
4. Пользователь может снять сломанный предмет.
5. Пользователь не может надеть сломанный предмет обратно.
6. Чтобы снова надеть предмет, его нужно починить.

## 9. Валюта

В MVP используется только валюта, без ресурсов.

Валюта отображается как:

```text
copper
silver
gold
```

Хранить в БД нужно одним числом:

```text
money_copper
```

Конвертация:

```text
100 copper = 1 silver
100 silver = 1 gold
```

## 10. Предметы

Типы предметов:

1. Экипировка — уникальные экземпляры.
2. Валюта — хранится на пользователе.

Ресурсы типа дерева/камня в MVP не реализуются, но могут быть добавлены позже.

## 11. Слоты экипировки

```text
weapon
helmet
armor
boots
ring
```

## 12. Типы оружия

```text
sword  -> warrior
dagger -> assassin
staff  -> mage
bow    -> archer
```

Оружие имеет классовые ограничения. Остальная экипировка универсальна.

## 13. Ранги предметов

`rarity` в API и БД хранит буквенный ранг предмета. Ранг также выводится из
уровня героя по тем же диапазонам.

| Ранг | key | Множитель | Уровни предмета/героя | Кол-во статов |
|---|---|---:|---:|---:|
| F | f | 1.0 | 1–10 | 1 |
| E | e | 1.25 | 11–20 | 1–2 |
| D | d | 1.6 | 21–30 | 2 |
| C | c | 2.0 | 31–40 | 2–3 |
| B | b | 2.5 | 41–50 | 3 |
| A | a | 3.1 | 51–60 | 3–4 |
| S | s | 3.8 | 61–70 | 4 |
| EX | ex | 4.6 | 71–80 | 4–5 |

Максимальный уровень предмета и героя в MVP: `80`.

## 14. Генерация предмета

Алгоритм:

```text
1. Выбирается dungeon location.
2. Проверяется item_drop_chance.
3. Если предмет выпал — выбираются связи `DungeonLocationItemTemplate` этой
   локации с активными `ItemTemplate`.
4. Templates фильтруются по классу героя.
5. Выбирается `item_template` weighted random по
   `DungeonLocationItemTemplate.chance`.
6. Rank/rarity берётся из `ItemTemplate.rarity_key`.
7. По rank/rarity выбирается item_level.
8. По rank/rarity выбирается количество статов.
9. Из possible_stats шаблона выбираются 1–3 характеристики.
10. Для каждой характеристики генерируется значение в min/max диапазоне.
11. Значение умножается на rarity multiplier и item level multiplier.
12. Создаётся reward draft в DungeonRun.items_reward JSON.
13. Реальный UserItem создаётся только при claim.
```

Формула усиления статов предмета:

```text
final_stat = base_stat * rarity_multiplier * (1 + item_level * 0.08)
```

## 15. Шансы редкости по стартовым локациям

### Старый лес

```json
{
  "f": 90,
  "e": 10,
  "d": 0,
  "c": 0,
  "b": 0,
  "a": 0,
  "s": 0,
  "ex": 0
}
```

### Заброшенная тропа

```json
{
  "f": 70,
  "e": 25,
  "d": 5,
  "c": 0,
  "b": 0,
  "a": 0,
  "s": 0,
  "ex": 0
}
```

### Сырая пещера

```json
{
  "f": 45,
  "e": 35,
  "d": 15,
  "c": 4,
  "b": 1,
  "a": 0,
  "s": 0,
  "ex": 0
}
```

## 16. Уровень героя

Максимальный уровень героя в MVP:

```text
80
```

Формула опыта до следующего уровня:

```text
experience_required = 100 * level ^ 1.5
```

## 17. Рост характеристик героя

Каждый уровень все классы получают:

```text
+5 health
+1 attack
+1 defense
```

Каждые 5 уровней применяется special growth из growth profile класса.

Пример growth profile:

```json
{
  "health_per_level": 5,
  "attack_per_level": 1,
  "defense_per_level": 1,
  "special_bonus_every": 5,
  "special_growth": {
    "critical_chance": 0.5,
    "evasion": 0
  }
}
```

## 18. Caps

```text
critical_chance max = 60%
evasion max = 50%
```

## 19. Централизация формул

Все игровые формулы должны быть вынесены в отдельный слой:

```text
GameFormulaService
GameBalanceService
GameConfigService
```

Формулы и коэффициенты не должны быть размазаны по коду.

Должны централизованно храниться:

```text
power formula
success chance formula
durability loss formula
reward calculation
repair cost formula
level experience formula
loot chance formula
rarity multipliers
stat caps
```
