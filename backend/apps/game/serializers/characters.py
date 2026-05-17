from rest_framework import serializers

from apps.game.i18n import message
from apps.game.models import Character, CharacterClass
from apps.game.services import GameFormulaService

from .common import localized_name, serializer_locale
from .inventory import UserItemSummarySerializer


class CharacterClassSerializer(serializers.ModelSerializer):
    """Сериализатор публичной карточки класса героя."""

    name = serializers.SerializerMethodField()
    start_stats = serializers.SerializerMethodField()

    class Meta:
        model = CharacterClass
        fields = ["key", "name", "start_stats"]

    def get_start_stats(self, obj):
        """Возвращает стартовые характеристики класса героя одним объектом."""

        return {
            "health": obj.start_health,
            "attack": obj.start_attack,
            "defense": obj.start_defense,
            "critical_chance": obj.start_critical_chance,
            "evasion": obj.start_evasion,
        }

    def get_name(self, obj):
        """Возвращает локализованное название класса героя."""

        return localized_name(obj, serializer_locale(self.context))


class CreateCharacterSerializer(serializers.Serializer):
    """Простой сериализатор входных данных для создания героя."""

    name = serializers.CharField(min_length=2, max_length=80)
    class_key = serializers.SlugField()

    def validate_class_key(self, value):
        """Проверяет, что выбранный класс существует и активен."""

        if not CharacterClass.objects.filter(key=value, is_active=True).exists():
            raise serializers.ValidationError(message("unknown_class", serializer_locale(self.context)))
        return value


class CharacterCreateSerializer(serializers.ModelSerializer):
    """Сериализатор создания героя и ответа с базовым прогрессом."""

    class_key = serializers.SlugField(write_only=True)

    class Meta:
        model = Character
        fields = ["id", "name", "class_key", "level", "experience"]
        read_only_fields = ["id", "level", "experience"]

    def validate_class_key(self, value):
        """Проверяет ключ активного класса героя."""

        if not CharacterClass.objects.filter(key=value, is_active=True).exists():
            raise serializers.ValidationError(message("unknown_class", serializer_locale(self.context)))
        return value

    def validate(self, attrs):
        """Запрещает создание второго героя на одном аккаунте."""

        user = self.context["request"].user
        if hasattr(user, "character"):
            raise serializers.ValidationError(message("character_exists", serializer_locale(self.context)))
        return attrs

    def create(self, validated_data):
        """Создаёт героя через сервис баланса с начальными характеристиками класса."""

        from apps.game.services import GameBalanceService

        class_key = validated_data.pop("class_key")
        character_class = CharacterClass.objects.get(key=class_key)
        return GameBalanceService.create_character(self.context["request"].user, validated_data["name"], character_class)

    def to_representation(self, instance):
        """Возвращает совместимый формат ответа после создания героя."""

        return {
            "id": instance.id,
            "name": instance.name,
            "class_key": instance.character_class_id,
            "level": instance.level,
            "experience": instance.experience,
        }


class CharacterMeSerializer(serializers.ModelSerializer):
    """Сериализатор полной карточки текущего героя."""

    class_info = serializers.SerializerMethodField()
    experience_to_next_level = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    equipment = serializers.SerializerMethodField()

    class Meta:
        model = Character
        fields = ["id", "name", "class_info", "level", "experience", "experience_to_next_level", "stats", "equipment"]

    def to_representation(self, instance):
        """Переименовывает class_info в поле class для API-контракта."""

        data = super().to_representation(instance)
        data["class"] = data.pop("class_info")
        return data

    def get_class_info(self, obj):
        """Возвращает ключ и локализованное название класса героя."""

        return {"key": obj.character_class_id, "name": localized_name(obj.character_class, serializer_locale(self.context))}

    def get_experience_to_next_level(self, obj):
        """Возвращает количество опыта, нужное для следующего уровня."""

        return GameFormulaService.experience_required(obj.level)

    def get_stats(self, obj):
        """Возвращает рассчитанные сервером характеристики героя."""

        return GameFormulaService.character_stats(obj)

    def get_equipment(self, obj):
        """Возвращает предметы, экипированные по слотам."""

        equipment = {slot: None for slot in ["weapon", "helmet", "armor", "boots", "ring"]}
        for item in obj.equipped_items.all():
            equipment[item.slot] = UserItemSummarySerializer(item).data
        return equipment
