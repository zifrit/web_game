SUPPORTED_LOCALES = {"en", "ru"}
DEFAULT_LOCALE = "en"


MESSAGES = {
    "email_already_registered": {
        "en": "Email already registered",
        "ru": "Email уже зарегистрирован",
    },
    "invalid_credentials": {
        "en": "Invalid email or password",
        "ru": "Неверный email или пароль",
    },
    "unknown_class": {
        "en": "Unknown class",
        "ru": "Неизвестный класс",
    },
    "character_exists": {
        "en": "User already has a character",
        "ru": "У пользователя уже есть герой",
    },
    "no_character": {
        "en": "User has no character.",
        "ru": "У пользователя нет героя.",
    },
    "active_run_exists": {
        "en": "Character already has an active dungeon run.",
        "ru": "У героя уже есть активный поход.",
    },
    "broken_items_block_run": {
        "en": "Broken equipped items block starting a new dungeon run.",
        "ru": "Сломанные надетые предметы блокируют запуск нового похода.",
    },
    "dungeon_not_found": {
        "en": "Dungeon location not found.",
        "ru": "Локация данжа не найдена.",
    },
    "run_not_owned": {
        "en": "Dungeon run does not belong to this user.",
        "ru": "Этот поход не принадлежит пользователю.",
    },
    "run_not_ready": {
        "en": "Dungeon run is not ready to claim.",
        "ru": "Поход еще не готов к получению награды.",
    },
    "item_fully_repaired": {
        "en": "Item is already fully repaired.",
        "ru": "Предмет уже полностью отремонтирован.",
    },
    "not_enough_money_repair": {
        "en": "Not enough money to repair this item.",
        "ru": "Недостаточно денег для ремонта предмета.",
    },
    "no_items_selected": {
        "en": "No items selected.",
        "ru": "Предметы не выбраны.",
    },
    "no_repair_needed": {
        "en": "Selected items do not need repair.",
        "ru": "Выбранные предметы не нуждаются в ремонте.",
    },
    "broken_item_equip": {
        "en": "Broken items cannot be equipped.",
        "ru": "Сломанные предметы нельзя экипировать.",
    },
    "class_not_allowed": {
        "en": "This item is not allowed for the character class.",
        "ru": "Этот предмет недоступен для класса героя.",
    },
    "equip_failed": {
        "en": "Could not equip item in this slot.",
        "ru": "Не удалось экипировать предмет в этот слот.",
    },
    "leaderboard_level_only": {
        "en": "Only level leaderboard is available in MVP.",
        "ru": "В MVP доступен только рейтинг по уровню.",
    },
}


def resolve_locale(value: str | None) -> str:
    if not value:
        return DEFAULT_LOCALE
    for part in value.split(","):
        code = part.split(";")[0].strip().lower().split("-")[0]
        if code in SUPPORTED_LOCALES:
            return code
    return DEFAULT_LOCALE


def request_locale(request) -> str:
    return resolve_locale(request.headers.get("Accept-Language") if request else None)


def translate(mapping: dict | None, locale: str, fallback: str = "") -> str:
    if not mapping:
        return fallback
    return mapping.get(locale) or mapping.get(DEFAULT_LOCALE) or mapping.get("ru") or fallback


def message(key: str, locale: str) -> str:
    return translate(MESSAGES.get(key), locale, key)
