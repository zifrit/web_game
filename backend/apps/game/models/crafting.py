from django.db import models

from .base import TimestampedModel
from .consumables import PotionTemplate
from .ingredients import IngredientTemplate


class CraftRecipe(TimestampedModel):
    """Рецепт крафта зелья: одна сложность = одно готовое зелье и набор слотов."""

    class Difficulty(models.TextChoices):
        SMALL = "small", "Малая"
        MEDIUM = "medium", "Средняя"
        LARGE = "large", "Большая"

    code = models.SlugField("Код", unique=True)
    difficulty = models.CharField("Сложность", max_length=16, choices=Difficulty.choices)
    potion = models.ForeignKey(
        PotionTemplate,
        verbose_name="Зелье",
        related_name="recipes",
        on_delete=models.PROTECT,
    )
    required_hero_level = models.PositiveIntegerField("Требуемый уровень героя", default=1)
    is_active = models.BooleanField("Активно", default=True)
    sort_order = models.PositiveIntegerField("Порядок сортировки", default=0)

    class Meta:
        ordering = ["sort_order", "code"]
        verbose_name = "Рецепт крафта"
        verbose_name_plural = "Рецепты крафта"

    def __str__(self) -> str:
        """Возвращает код рецепта и связанное зелье."""

        return f"{self.code} -> {self.potion}"


class CraftRecipeIngredient(TimestampedModel):
    """Слот рецепта: ингредиент и его количество на ОДНО сваренное зелье."""

    recipe = models.ForeignKey(
        CraftRecipe,
        verbose_name="Рецепт",
        related_name="ingredients",
        on_delete=models.CASCADE,
    )
    ingredient = models.ForeignKey(
        IngredientTemplate,
        verbose_name="Ингредиент",
        related_name="recipe_links",
        on_delete=models.PROTECT,
    )
    quantity = models.PositiveSmallIntegerField("Количество на одно зелье")

    class Meta:
        unique_together = ("recipe", "ingredient")
        verbose_name = "Ингредиент рецепта"
        verbose_name_plural = "Ингредиенты рецепта"

    def __str__(self) -> str:
        """Возвращает связку рецепта, ингредиента и количества."""

        return f"{self.recipe} — {self.ingredient} x{self.quantity}"
