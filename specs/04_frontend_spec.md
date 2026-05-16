# 04. Frontend Specification

## 1. Frontend stack

```text
Next.js
React
TypeScript
Tailwind CSS
TanStack Query
React Hook Form
Zod
Zustand optional
```

## 2. Назначение библиотек

### Next.js

Фреймворк для React-приложения.

### TypeScript

Типизация API, компонентов, игровых моделей.

### Tailwind CSS

Быстрая стилизация UI без создания большого количества CSS-файлов.

### TanStack Query

Работа с серверными данными:

- кеширование;
- loading/error состояния;
- refetch;
- invalidation;
- работа с API-запросами.

### React Hook Form

Формы:

- регистрация;
- логин;
- создание героя.

### Zod

Runtime-валидация форм и данных.

### Zustand

Опционально для глобального состояния:

- token;
- user;
- UI-состояние.

Не тащить Redux в MVP.

## 3. Главный player flow

```text
Login/Register
↓
Create Character
↓
Character Screen
↓
Dungeons Screen
↓
Start Run
↓
Current Run Timer
↓
Claim Reward
↓
Inventory
↓
Equip / Repair
↓
Repeat
```

## 4. Экраны MVP

### 4.1 Auth screens

- Login
- Register

Поля:

```text
email
password
```

После регистрации пользователь сразу получает JWT и попадает на создание героя.

### 4.2 Create Character screen

Данные:

- список классов из `GET /character-classes`;
- имя героя;
- выбор класса.

Показывать стартовые статы класса.

### 4.3 Character screen

Главный экран игрока.

Показывает:

```text
имя
класс
уровень
опыт
experience_to_next_level
health
attack
defense
critical_chance
evasion
power
валюта
экипировка
```

Кнопки:

```text
Dungeons
Inventory
Leaderboard
```

### 4.4 Dungeons screen

Список доступных локаций.

Карточка локации:

```text
картинка
название
описание
время
required_power
success_chance
item_drop_chance
preview наград
кнопка Start
```

Если герой уже в походе, показывать текущий поход и таймер.

### 4.5 Current Run / Reward Modal

Если поход идёт:

```text
название локации
оставшееся время
таймер
```

Если поход завершён:

```text
SUCCESS / FAILED
опыт
валюта
количество предметов
durability_loss
кнопка Claim Reward
```

### 4.6 Inventory screen

Инвентарь должен быть лёгким.

`GET /inventory` возвращает:

- summary бонусов экипировки;
- equipped slots;
- список коротких карточек предметов.

Карточка предмета:

```text
иконка
rarity
broken state
```

По клику:

```text
GET /inventory/items/{item_id}
```

Открывается детальная карточка:

```text
название
изображение
уровень предмета
редкость
статы
прочность
можно ли надеть
кнопка Equip / Unequip
кнопка Repair, если durability_current < durability_max
```

### 4.7 Repair flow

```text
1. Пользователь открыл предмет.
2. Если durability_current < durability_max, показывается кнопка Repair.
3. Нажатие Repair вызывает GET /repair-preview.
4. UI показывает стоимость ремонта.
5. Пользователь подтверждает.
6. POST /repair.
7. Инвентарь и валюта обновляются.
```

### 4.8 Leaderboard screen

MVP:

```text
Top by level
```

Показывать:

```text
rank
character name
class
level
avatar
```

## 5. UX-правила

- Клиент не считает игровые формулы.
- Клиент показывает значения, полученные с сервера.
- Таймер может считаться на клиенте от `ends_at`, но результат похода подтверждает сервер.
- После equip/unequip/repair нужно инвалидировать queries персонажа и инвентаря.
- Если сломанный предмет в активном слоте, при попытке start dungeon показывать ошибку сервера.

## 6. Что не делать в MVP

- Не делать сложную карту мира.
- Не делать real-time websocket.
- Не делать drag-and-drop inventory как обязательное требование.
- Не делать анимации боя.
- Не делать отдельную админку на фронте.
- Не делать Redux.
