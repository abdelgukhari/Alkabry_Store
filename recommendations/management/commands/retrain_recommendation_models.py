from django.core.management.base import BaseCommand
from recommendations.services import RecommendationService


class Command(BaseCommand):
    help = 'Recompute recommendation matrices and retrain cached recommendation models.'

    def handle(self, *args, **options):
        service = RecommendationService()
        service.reset_models()
        self.stdout.write(self.style.SUCCESS('Recommendation models have been reset and retrained.'))
