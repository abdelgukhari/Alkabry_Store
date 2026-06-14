from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.utils import timezone
from recommendations.services import RecommendationService


class Command(BaseCommand):
    help = 'Re-evaluate all recommendation algorithms and prime the evaluation cache.'

    def handle(self, *args, **options):
        service = RecommendationService()
        self.stdout.write(self.style.SUCCESS('Re-evaluating and priming algorithm cache...'))

        for algo in service.ALGORITHMS:
            self.stdout.write(f'  Evaluating {algo}... ', ending='')
            metrics = service.evaluate_algorithm(algo)
            if not metrics:
                self.stdout.write(self.style.WARNING('no data'))
                continue

            cache_key = f'algo_eval_{algo}'
            cache.set(cache_key, metrics, 60 * 60 * 24)
            self.stdout.write(self.style.SUCCESS('cached'))

        self.stdout.write(self.style.SUCCESS('Algorithm evaluation cache primed successfully.'))
