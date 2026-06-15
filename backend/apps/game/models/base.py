from django.db import models


def media_asset_upload_path(instance: "MediaAsset", filename: str) -> str:
    """Формирует путь файла медиа-ассета внутри настроенного хранилища."""

    return f"media-assets/{instance.pk or 'new'}/{filename}"


class TimestampedModel(models.Model):
    """Абстрактная модель с датами создания и последнего обновления записи."""

    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)

    class Meta:
        abstract = True


class MediaAsset(TimestampedModel):
    """Набор файлов одного медиа-ассета в разных размерах для S3-хранилища."""

    class AssetType(models.TextChoices):
        CHARACTERS = "characters", "Персонажи"
        CUSTOM = "custom", "Пользовательские"
        ICONS = "icons", "Иконки"
        WEAPONS = "weapons", "Оружие"
        DUNGEONS = "dungeons", "Данжи"
        POTION = "potion", "Зелья"
        INGREDIENT = "ingredient", "Ингредиенты"
        CHESTS = "chests", "Сундуки"
        MAP = "map", "Карта"
        BOSSES = "bosses", "Боссы"
        SCROLLS = "scrolls", "Свитки"

    name = models.CharField("Название", max_length=120, blank=True, default="")
    asset_type = models.CharField("Тип", max_length=20, choices=AssetType.choices, null=True, blank=True)
    original = models.FileField("Оригинальный файл", upload_to=media_asset_upload_path, blank=True, default="")
    large = models.FileField("Большой файл 512x512", upload_to=media_asset_upload_path, blank=True, default="")
    medium = models.FileField("Средний файл 256x256", upload_to=media_asset_upload_path, blank=True, default="")
    small = models.FileField("Малый файл 128x128", upload_to=media_asset_upload_path, blank=True, default="")

    class Meta:
        verbose_name = "Медиа-ассет"
        verbose_name_plural = "Медиа-ассеты"

    @staticmethod
    def _file_url(file_field) -> str:
        """Безопасно возвращает URL файла из настроенного Django storage."""

        if not file_field:
            return ""
        try:
            return file_field.url
        except ValueError:
            return ""

    @property
    def original_url(self) -> str:
        """Возвращает URL оригинального файла из S3 или локального storage."""

        return self._file_url(self.original)

    @property
    def large_url(self) -> str:
        """Возвращает URL большой версии файла."""

        return self._file_url(self.large)

    @property
    def medium_url(self) -> str:
        """Возвращает URL средней версии файла."""

        return self._file_url(self.medium)

    @property
    def small_url(self) -> str:
        """Возвращает URL малой версии файла."""

        return self._file_url(self.small)

    def __str__(self) -> str:
        """Возвращает название, основной URL ассета или техническое имя записи."""

        return self.name or self.original_url or f"Media #{self.pk}"
