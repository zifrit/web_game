from django.utils import timezone
from rest_framework import serializers

from apps.game.i18n import DEFAULT_LOCALE, translate
from apps.game.models import DungeonLocation, DungeonRun, DungeonRunStatus
from apps.game.services import GameFormulaService

from .common import localized_item_name, localized_name, media_payload, serializer_locale


class DungeonLocationSerializer(serializers.ModelSerializer):
    """Сериализатор локации подземелья для списка и детальной карточки."""

    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    success_chance = serializers.SerializerMethodField()
    media = serializers.SerializerMethodField()
    rewards_preview = serializers.SerializerMethodField()

    class Meta:
        model = DungeonLocation
        fields = [
            "id",
            "name",
            "description",
            "duration_seconds",
            "required_power",
            "success_chance",
            "item_drop_chance",
            "media",
            "rewards_preview",
        ]

    def get_success_chance(self, obj):
        """Считает шанс успеха текущего героя в этой локации."""

        character_power = self.context.get("character_power")
        if character_power is None:
            character = self.context.get("character")
            if not character:
                return None
            character_power = GameFormulaService.character_stats(character)["power"]
        return GameFormulaService.success_chance(character_power, obj.required_power)

    def get_name(self, obj):
        """Возвращает локализованное название подземелья."""

        return localized_name(obj, serializer_locale(self.context))

    def get_description(self, obj):
        """Возвращает локализованное описание подземелья."""

        locale = serializer_locale(self.context)
        return translate(obj.description_i18n, locale, obj.description)

    def get_media(self, obj):
        """Возвращает набор URL медиа для подземелья."""

        return media_payload(obj.media, self.context)

    def get_rewards_preview(self, obj):
        """Возвращает диапазоны возможных наград за успех."""

        return {
            "experience": {"min": obj.experience_min, "max": obj.experience_max},
            "money_copper": {"min": obj.money_min_copper, "max": obj.money_max_copper},
        }


class DungeonRunSerializer(serializers.ModelSerializer):
    """Сериализатор активного или завершённого забега в подземелье."""

    location = serializers.SerializerMethodField()
    remaining_seconds = serializers.SerializerMethodField()
    result_preview = serializers.SerializerMethodField()

    class Meta:
        model = DungeonRun
        fields = [
            "id",
            "status",
            "location",
            "started_at",
            "ends_at",
            "remaining_seconds",
            "success_chance",
            "result_preview",
        ]

    def get_location(self, obj):
        """Возвращает краткую локализованную карточку локации забега."""

        return {"id": obj.location_id, "name": localized_name(obj.location, serializer_locale(self.context))}

    def get_remaining_seconds(self, obj):
        """Возвращает оставшиеся секунды до конца активного забега."""

        if obj.status != DungeonRunStatus.IN_PROGRESS:
            return None
        return max(0, int((obj.ends_at - timezone.now()).total_seconds()))

    def get_result_preview(self, obj):
        """Возвращает предварительный итог завершённого забега до claim."""

        if obj.status == DungeonRunStatus.IN_PROGRESS:
            return None
        return {
            "is_success": obj.is_success,
            "experience": obj.experience_reward or 0,
            "money_copper": obj.money_reward_copper or 0,
            "items_count": len(obj.items_reward or []),
            "durability_loss": obj.durability_loss or 0,
        }


class DungeonRunStartSerializer(serializers.Serializer):
    """Сериализатор запроса на запуск подземелья."""

    location_id = serializers.IntegerField(min_value=1)


class ClaimResponseSerializer:
    """Рендер ответа получения наград за забег."""

    @staticmethod
    def render(result, locale=DEFAULT_LOCALE):
        """Преобразует результат claim в публичный API-ответ."""

        item_context: dict = {}
        return {
            "id": result.run.id,
            "status": result.run.status,
            "is_success": result.run.is_success,
            "success_chance": result.run.success_chance,
            "rewards": {
                "experience": result.claim.experience_claimed,
                "money_copper": result.claim.money_claimed_copper,
                "items": [
                    {
                        "id": item.id,
                        "name": localized_item_name(item, locale, item_context),
                        "rarity": item.rarity,
                        "item_level": item.item_level,
                        "stats": item.stats or {},
                        "durability": {"current": item.durability_current, "max": item.durability_max},
                    }
                    for item in result.items
                ],
                "durability_loss": result.run.durability_loss or 0,
            },
            "level_up": {"old_level": result.old_level, "new_level": result.new_level},
        }


class DungeonRunHistorySerializer(serializers.ModelSerializer):
    """Сериализатор строки истории завершённых забегов."""

    location_name = serializers.SerializerMethodField()
    claimed_at = serializers.SerializerMethodField()

    class Meta:
        model = DungeonRun
        fields = ["id", "location_name", "status", "is_success", "started_at", "claimed_at"]

    def get_claimed_at(self, obj):
        """Возвращает дату получения награды, если она уже была получена."""

        claim = getattr(obj, "claim", None)
        return claim.created_at if claim else None

    def get_location_name(self, obj):
        """Возвращает локализованное название локации из истории."""

        return localized_name(obj.location, serializer_locale(self.context))
