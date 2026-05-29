from django.apps import AppConfig
from django.db.models.signals import post_delete, post_save


class GameConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.game"
    label = "game"

    def ready(self):
        from . import models, services

        post_save.connect(services._invalidate_game_config_cache, sender=models.GameConfig)
        post_delete.connect(services._invalidate_game_config_cache, sender=models.GameConfig)
        post_save.connect(services._invalidate_rarity_config_cache, sender=models.RarityConfig)
        post_delete.connect(services._invalidate_rarity_config_cache, sender=models.RarityConfig)

