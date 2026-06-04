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
    "totp_already_enabled": {
        "en": "Two-factor protection is already enabled.",
        "ru": "Двухфакторная защита уже включена.",
    },
    "totp_not_configured": {
        "en": "Two-factor protection is not configured.",
        "ru": "Двухфакторная защита не настроена.",
    },
    "totp_setup_required": {
        "en": "Start two-factor setup before confirming it.",
        "ru": "Сначала начните настройку двухфакторной защиты.",
    },
    "invalid_totp_code": {
        "en": "Invalid two-factor code.",
        "ru": "Неверный код двухфакторной защиты.",
    },
    "invalid_totp_challenge": {
        "en": "Two-factor login challenge expired. Log in again.",
        "ru": "Проверка двухфакторного входа истекла. Войдите снова.",
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
    "unclaimed_run_exists": {
        "en": "Claim the reward for the finished dungeon run before starting a new one.",
        "ru": "Сначала заберите награду за завершенный поход, затем запускайте новый.",
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
    "mini_game_not_available": {
        "en": "Mini-game is not available for this dungeon run.",
        "ru": "Мини-игра недоступна для этого похода.",
    },
    "mini_game_run_not_active": {
        "en": "Mini-game can only be started during an active dungeon run.",
        "ru": "Мини-игру можно запустить только во время активного похода.",
    },
    "mini_game_already_finished": {
        "en": "Mini-game attempt for this dungeon run is already finished.",
        "ru": "Попытка мини-игры для этого похода уже завершена.",
    },
    "mini_game_attempt_not_found": {
        "en": "Mini-game attempt not found.",
        "ru": "Попытка мини-игры не найдена.",
    },
    "mini_game_invalid_move": {
        "en": "Invalid mini-game move.",
        "ru": "Недопустимый ход мини-игры.",
    },
    "mini_game_card_already_matched": {
        "en": "This mini-game card is already matched.",
        "ru": "Эта карточка мини-игры уже найдена.",
    },
    "mini_game_expired": {
        "en": "Mini-game timer expired.",
        "ru": "Таймер мини-игры истек.",
    },
    "mini_game_busy": {
        "en": "Previous mini-game move is still being processed.",
        "ru": "Предыдущий ход мини-игры еще обрабатывается.",
    },
    "mini_game_config_required": {
        "en": "Select a mini-game difficulty to start.",
        "ru": "Выберите сложность мини-игры для запуска.",
    },
    "mini_game_config_invalid": {
        "en": "Selected mini-game difficulty is not available.",
        "ru": "Выбранная сложность мини-игры недоступна.",
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
    "leaderboard_type_invalid": {
        "en": "Unknown leaderboard type. Use 'level' or 'power'.",
        "ru": "Неизвестный тип рейтинга. Используйте «level» или «power».",
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
