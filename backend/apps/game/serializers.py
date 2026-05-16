from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Character, CharacterClass, DungeonLocation, DungeonRun, DungeonRunStatus, UserItem
from .services import GameFormulaService, InventoryService


def media_payload(media):
    if not media:
        return None
    return {
        "icon_url": media.icon_url,
        "small_url": media.small_url,
        "medium_url": media.medium_url,
        "large_url": media.large_url,
    }


def token_response(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access_token": str(refresh.access_token),
        "refresh_token": str(refresh),
        "user": {
            "id": user.id,
            "email": user.email,
            "has_character": hasattr(user, "character"),
        },
    }


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)

    def validate_email(self, value):
        from .models import User

        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already registered")
        return value

    def create(self, validated_data):
        from .models import User

        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs["email"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid email or password")
        attrs["user"] = user
        return attrs


class CharacterClassSerializer(serializers.ModelSerializer):
    start_stats = serializers.SerializerMethodField()

    class Meta:
        model = CharacterClass
        fields = ["key", "name", "start_stats"]

    def get_start_stats(self, obj):
        return {
            "health": obj.start_health,
            "attack": obj.start_attack,
            "defense": obj.start_defense,
            "critical_chance": obj.start_critical_chance,
            "evasion": obj.start_evasion,
        }


class CreateCharacterSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=2, max_length=80)
    class_key = serializers.SlugField()

    def validate_class_key(self, value):
        if not CharacterClass.objects.filter(key=value, is_active=True).exists():
            raise serializers.ValidationError("Unknown class")
        return value


class CharacterCreateSerializer(serializers.ModelSerializer):
    class_key = serializers.SlugField(write_only=True)

    class Meta:
        model = Character
        fields = ["id", "name", "class_key", "level", "experience"]
        read_only_fields = ["id", "level", "experience"]

    def validate_class_key(self, value):
        if not CharacterClass.objects.filter(key=value, is_active=True).exists():
            raise serializers.ValidationError("Unknown class")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        if hasattr(user, "character"):
            raise serializers.ValidationError("User already has a character")
        return attrs

    def create(self, validated_data):
        from .services import GameBalanceService

        class_key = validated_data.pop("class_key")
        character_class = CharacterClass.objects.get(key=class_key)
        return GameBalanceService.create_character(self.context["request"].user, validated_data["name"], character_class)

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "name": instance.name,
            "class_key": instance.character_class_id,
            "level": instance.level,
            "experience": instance.experience,
        }


class CharacterMeSerializer(serializers.ModelSerializer):
    class_info = serializers.SerializerMethodField()
    experience_to_next_level = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()
    equipment = serializers.SerializerMethodField()

    class Meta:
        model = Character
        fields = ["id", "name", "class_info", "level", "experience", "experience_to_next_level", "stats", "equipment"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["class"] = data.pop("class_info")
        return data

    def get_class_info(self, obj):
        return {"key": obj.character_class_id, "name": obj.character_class.name}

    def get_experience_to_next_level(self, obj):
        return GameFormulaService.experience_required(obj.level)

    def get_stats(self, obj):
        return GameFormulaService.character_stats(obj)

    def get_equipment(self, obj):
        equipment = {slot: None for slot in ["weapon", "helmet", "armor", "boots", "ring"]}
        for item in obj.equipped_items.all():
            equipment[item.slot] = UserItemSummarySerializer(item).data
        return equipment


class DungeonLocationSerializer(serializers.ModelSerializer):
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
        character = self.context.get("character")
        if not character:
            return None
        power = GameFormulaService.character_stats(character)["power"]
        return GameFormulaService.success_chance(power, obj.required_power)

    def get_media(self, obj):
        return media_payload(obj.media)

    def get_rewards_preview(self, obj):
        return {
            "experience": {"min": obj.experience_min, "max": obj.experience_max},
            "money_copper": {"min": obj.money_min_copper, "max": obj.money_max_copper},
        }


class DungeonRunSerializer(serializers.ModelSerializer):
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
        return {"id": obj.location_id, "name": obj.location.name}

    def get_remaining_seconds(self, obj):
        if obj.status != DungeonRunStatus.IN_PROGRESS:
            return None
        return max(0, int((obj.ends_at - timezone.now()).total_seconds()))

    def get_result_preview(self, obj):
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
    location_id = serializers.IntegerField(min_value=1)


class UserItemSummarySerializer(serializers.ModelSerializer):
    icon_url = serializers.SerializerMethodField()
    is_broken = serializers.BooleanField(read_only=True)

    class Meta:
        model = UserItem
        fields = ["id", "icon_url", "rarity", "is_broken"]

    def get_icon_url(self, obj):
        return obj.template.media.icon_url if obj.template.media else ""


class UserItemDetailSerializer(serializers.ModelSerializer):
    durability = serializers.SerializerMethodField()
    is_equipped = serializers.SerializerMethodField()
    is_broken = serializers.BooleanField(read_only=True)
    can_equip = serializers.SerializerMethodField()
    media = serializers.SerializerMethodField()

    class Meta:
        model = UserItem
        fields = [
            "id",
            "name",
            "slot",
            "item_type",
            "rarity",
            "item_level",
            "stats",
            "durability",
            "is_equipped",
            "is_broken",
            "can_equip",
            "media",
        ]

    def get_durability(self, obj):
        return {"current": obj.durability_current, "max": obj.durability_max}

    def get_is_equipped(self, obj):
        character = self.context.get("character")
        return bool(character and obj.equipped_character_id == character.id)

    def get_can_equip(self, obj):
        character = self.context.get("character")
        return bool(character and InventoryService.can_equip(obj, character))

    def get_media(self, obj):
        return media_payload(obj.template.media)


class ClaimResponseSerializer:
    @staticmethod
    def render(result):
        return {
            "id": result.run.id,
            "status": result.run.status,
            "is_success": result.run.is_success,
            "rewards": {
                "experience": result.claim.experience_claimed,
                "money_copper": result.claim.money_claimed_copper,
                "items": [
                    {"id": item.id, "name": item.name, "rarity": item.rarity, "item_level": item.item_level}
                    for item in result.items
                ],
                "durability_loss": result.run.durability_loss or 0,
            },
            "level_up": {"old_level": result.old_level, "new_level": result.new_level},
        }


class DungeonRunHistorySerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source="location.name")
    claimed_at = serializers.SerializerMethodField()

    class Meta:
        model = DungeonRun
        fields = ["id", "location_name", "status", "is_success", "started_at", "claimed_at"]

    def get_claimed_at(self, obj):
        claim = getattr(obj, "claim", None)
        return claim.created_at if claim else None


class InventorySerializer:
    @staticmethod
    def render(character):
        equipment = {slot: None for slot in ["weapon", "helmet", "armor", "boots", "ring"]}
        for item in character.equipped_items.all():
            equipment[item.slot] = UserItemSummarySerializer(item).data
        items = UserItem.objects.filter(owner_user=character.user).select_related("template__media")
        return {
            "equipment_summary": InventoryService.equipment_summary(character),
            "equipped": equipment,
            "items": UserItemSummarySerializer(items, many=True).data,
        }


class LeaderboardItemSerializer:
    @staticmethod
    def render(items, my_character):
        payload = [
            {
                "rank": index + 1,
                "character_id": character.id,
                "character_name": character.name,
                "class": {"key": character.character_class_id, "name": character.character_class.name},
                "level": character.level,
                "avatar": media_payload(character.avatar_media),
            }
            for index, character in enumerate(items)
        ]
        my_rank = None
        if my_character:
            better = Character.objects.filter(level__gt=my_character.level).count()
            same_level_better = Character.objects.filter(level=my_character.level, experience__gt=my_character.experience).count()
            my_rank = {"rank": better + same_level_better + 1, "character_id": my_character.id, "level": my_character.level}
        return {"type": "level", "items": payload, "my_rank": my_rank}
