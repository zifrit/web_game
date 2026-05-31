from django.core.management.base import BaseCommand

from apps.game.seed_data import seed_ranked_item_templates


class Command(BaseCommand):
    help = "Seed ranked F-EX item templates for all equipment kinds."

    def handle(self, *args, **options):
        templates = seed_ranked_item_templates()
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(templates)} ranked item templates."))
