from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.game.models import DungeonMiniGameConfig, MiniGameCardFace
from apps.game.models.dungeons import sanitize_svg_markup


class SanitizeSvgMarkupTests(TestCase):
    def test_strips_script_event_handlers_and_external_href(self):
        dirty = (
            '<svg onload="x()"><script>alert(1)</script>'
            '<a href="https://evil.test">x</a>'
            '<use xlink:href="#safe"/></svg>'
        )
        cleaned = sanitize_svg_markup(dirty)
        self.assertNotIn("<script", cleaned)
        self.assertNotIn("onload", cleaned)
        self.assertNotIn("https://evil.test", cleaned)
        # Внутренние ссылки на якоря остаются.
        self.assertIn("#safe", cleaned)

    def test_save_sanitizes_markup(self):
        face = MiniGameCardFace.objects.create(
            code="danger",
            svg_markup='<svg onclick="bad()"><rect/></svg>',
        )
        face.refresh_from_db()
        self.assertNotIn("onclick", face.svg_markup)


class DungeonMiniGameConfigValidationTests(TestCase):
    def setUp(self):
        for index, code in enumerate(["a", "b", "c", "d", "e", "f"]):
            MiniGameCardFace.objects.create(code=code, svg_markup="<svg/>", sort_order=index)

    def _config(self, **overrides):
        data = {
            "name": "cfg",
            "difficulty": "6",
            "pairs_count": 6,
            "time_limit_seconds": 60,
            "reward_duration_reduction_percent": 10,
            "max_reduction_seconds": 120,
            "card_face_codes": ["a", "b", "c", "d", "e", "f"],
        }
        data.update(overrides)
        return DungeonMiniGameConfig(**data)

    def test_valid_config_passes(self):
        self._config().clean()

    def test_rejects_fewer_codes_than_pairs(self):
        with self.assertRaises(ValidationError):
            self._config(card_face_codes=["a", "b", "c"]).clean()

    def test_rejects_unknown_code(self):
        with self.assertRaises(ValidationError):
            self._config(card_face_codes=["a", "b", "c", "d", "e", "zzz"]).clean()

    def test_rejects_inactive_code(self):
        MiniGameCardFace.objects.filter(code="f").update(is_active=False)
        with self.assertRaises(ValidationError):
            self._config().clean()

    def test_rejects_duplicate_codes(self):
        with self.assertRaises(ValidationError):
            self._config(card_face_codes=["a", "a", "b", "c", "d", "e"]).clean()
