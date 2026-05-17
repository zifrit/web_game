# Browser RPG — Design System & UI Specification v1

## Общая концепция

Проект представляет собой браузерную async/idle RPG в стиле Diablo-like интерфейсов.

Основные визуальные ассоциации:
- Diablo II / Diablo IV
- Path of Exile
- Torchlight
- Grim Dawn
- Last Epoch

Но:
- без перегруженного dark fantasy;
- без чрезмерной реалистичности;
- с более чистым и читаемым интерфейсом.

Основная задача дизайна:
- создать ощущение progression-driven RPG;
- подчеркнуть ценность предметов и экипировки;
- сделать интерфейс атмосферным, но удобным;
- сохранить простоту MVP.

---

# Основное визуальное направление

## Стиль

```text
Dark Fantasy UI
Diablo-like
Medieval UI
Clean RPG Panels
```

Интерфейс:
- тёмный;
- контрастный;
- металлические/каменные элементы;
- холодные оттенки;
- светящиеся акценты;
- читаемые карточки.

Не использовать:
- кислотные цвета;
- мультяшный стиль;
- mobile-casual стилистику;
- flat pastel UI.

---

# Цветовая палитра

## Основной фон

| Назначение | Цвет |
|---|---|
| Main Background | #0B1020 |
| Secondary Background | #111827 |
| Card Background | #1A2235 |
| Elevated Card | #202B44 |
| Border | #2E3B5A |
| Hover Border | #4B6AA3 |

---

## Основные акценты

| Назначение | Цвет |
|---|---|
| Primary Blue | #3B82F6 |
| Deep Blue | #2563EB |
| Bright Accent | #60A5FA |
| Cyan Accent | #38BDF8 |

Использовать:
- для кнопок;
- hover-состояний;
- выделений;
- активных слотов.

---

## Цвета редкости предметов

| Редкость | Цвет |
|---|---|
| common | #9CA3AF |
| uncommon | #22C55E |
| rare | #3B82F6 |
| epic | #A855F7 |

Цвет редкости:
- используется для названия предмета;
- glow-эффекта;
- рамки карточки предмета.

---

## Статусы

| Назначение | Цвет |
|---|---|
| Success | #22C55E |
| Error | #EF4444 |
| Warning | #F59E0B |
| Info | #38BDF8 |

---

# Типографика

## Основной шрифт

### Inter

Использование:
- UI;
- описания;
- характеристики;
- кнопки;
- формы.

Вес:

| Назначение | Weight |
|---|---|
| Regular Text | 400 |
| Medium UI | 500 |
| Headers | 700 |

---

## RPG-заголовки

### Cinzel

Использование:
- названия экранов;
- названия данжей;
- логотип;
- заголовки карточек.

Не использовать для большого текста.

---

# Размеры текста

| Назначение | Размер |
|---|---|
| Small Meta | 12px |
| Standard UI | 14px |
| Main Text | 16px |
| Card Headers | 18px |
| Screen Headers | 24px |
| Main Logo | 36px |

---

# Layout

## Основной контейнер

```text
max-width: 1400px
padding: 24px
```

Интерфейс desktop-first.

Минимальная поддержка mobile:
- адаптивность;
- вертикальное расположение панелей.

Но MVP в первую очередь рассчитан на desktop.

---

# Главный экран персонажа

## Layout

Экран делится на 3 блока:

```text
[ Character Panel ] [ Main Content ] [ Inventory/Stats ]
```

---

## Character Panel

Содержит:
- portrait;
- level;
- class;
- power;
- health;
- attack;
- defense;
- crit;
- evasion.

Визуально:
- тёмная карточка;
- синяя рамка;
- лёгкий glow.

---

## Main Content

Содержит:
- список данжей;
- активный поход;
- таймер;
- claim rewards.

Карточки данжей:
- большая иллюстрация;
- название;
- required power;
- success chance;
- rewards preview.

---

## Inventory Panel

Grid-based layout.

Размер карточки:

```text
64x64
или
72x72
```

Карточка:
- icon;
- rarity border;
- broken overlay;
- hover glow.

---

# Inventory UX

## Minimal Inventory Response

Inventory screen сначала показывает:
- icon;
- rarity;
- broken status.

Подробности открываются по click.

---

## Item Modal

При открытии предмета:

Показывается:
- название;
- rarity;
- item level;
- stats;
- durability;
- equip/unequip;
- repair button.

---

## Broken Items

Broken item:
- затемняется;
- имеет красную иконку warning;
- показывает durability 0/max.

---

# Dungeon Screen

## Dungeon Card

Содержит:
- artwork;
- dungeon name;
- duration;
- required power;
- success chance;
- rewards preview.

---

## Active Dungeon State

Показывается:
- progress timer;
- current dungeon;
- remaining time.

Использовать:
- progress bar;
- blue animated glow.

---

# Buttons

## Основная кнопка

```text
background: #2563EB
hover: #3B82F6
text: white
border-radius: 10px
padding: 12px 18px
```

---

## Secondary Button

```text
background: transparent
border: 1px solid #3B82F6
```

---

## Danger Button

```text
background: #EF4444
```

---

# Effects

Использовать умеренно:
- glow;
- hover border;
- fade animation;
- tooltip animations.

Не использовать:
- excessive particles;
- heavy motion;
- screen shake;
- autoplay animations.

---

# Shadows

Использовать мягкие холодные тени:

```css
box-shadow:
0 0 12px rgba(59, 130, 246, 0.15)
```

---

# Borders

Основной стиль:

```css
border: 1px solid #2E3B5A
```

Hover:

```css
border-color: #4B6AA3
```

---

# Scrollbars

Кастомные scrollbars:
- тёмные;
- синие hover-состояния;
- тонкие.

---

# UI Principles

## Основные правила

### 1. Информация важнее декора

Игрок должен быстро видеть:
- что надето;
- что лучше;
- что сломано;
- что можно улучшить.

---

### 2. Редкость должна ощущаться

Rare/Epic предметы:
- glow;
- цвет;
- лёгкий shine.

Но без визуального мусора.

---

### 3. Минимум визуального шума

Не перегружать:
- background textures;
- ornaments;
- excessive gradients.

---

### 4. Быстрый игровой цикл

Игрок должен за 2–3 клика:
- начать данж;
- забрать награду;
- надеть предмет.

---

# Tailwind Guidelines

## Использовать

```text
rounded-xl
rounded-2xl
backdrop-blur
border-slate
shadow-blue
```

---

## Не использовать

```text
rainbow gradients
glassmorphism overload
bright neon cyberpunk
```

---

# Responsive Rules

## Desktop-first

Главная цель MVP:
- desktop browser experience.

---

## Mobile

На mobile:
- панели становятся вертикальными;
- inventory grid уменьшается;
- dungeon cards stack vertically.

---

# Animation Rules

Использовать:
- fade-in;
- subtle hover scale;
- soft transitions.

Длительность:

```text
150ms–250ms
```

---

# Design Goals

Интерфейс должен ощущаться как:

```text
Loot-driven RPG
Dark Fantasy Dashboard
Async Adventure Interface
```

А НЕ как:

```text
Mobile casino
Anime gacha
Casual clicker
Enterprise admin panel
```

---

# MVP Priority

Приоритеты дизайна:

```text
1. Читаемость
2. Скорость взаимодействия
3. Атмосфера
4. Редкость предметов
5. Анимации
```

А не наоборот.

