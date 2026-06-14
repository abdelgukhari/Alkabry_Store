"""
Run comprehensive algorithm comparison across all 5 recommendation
algorithms and save the results as a ComparisonReport.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from recommendations.services import RecommendationService
from analytics.models import ComparisonReport


class Command(BaseCommand):
    help = 'Run comprehensive algorithm comparison'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('RECOMMENDATION ALGORITHM COMPARISON'))
        self.stdout.write(self.style.SUCCESS('='*70))
        
        service = RecommendationService()
        
        self.stdout.write('\nEvaluating algorithms...\n')
        evaluations = {}
        
        for algo in service.ALGORITHMS:
            self.stdout.write(f'  Evaluating {algo}...', ending='')
            try:
                metrics = service.evaluate_algorithm(algo)
                if metrics:
                    evaluations[algo] = metrics
                    accuracy = metrics.get('accuracy', 0) * 100
                    self.stdout.write(self.style.SUCCESS(
                        f' Accuracy: {accuracy:.1f}% | '
                        f'Hit Rate: {metrics["hit_rate"]*100:.1f}% | '
                        f'Precision: {metrics["precision"]:.4f} | '
                        f'MRR: {metrics["mrr"]:.4f}'
                    ))
                else:
                    self.stdout.write(self.style.WARNING(' Not enough data'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f' Error: {e}'))
        
        if not evaluations:
            self.stdout.write(self.style.ERROR('\nNo evaluations completed.'))
            self.stdout.write(self.style.WARNING('Run: python manage.py generate_dataset --clear'))
            return
        
        # Rank
        scores = {}
        for algo, metrics in evaluations.items():
            scores[algo] = metrics.get('accuracy', 0)
        
        ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Display
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('FINAL RANKINGS'))
        self.stdout.write(self.style.SUCCESS('='*70))
        
        for i, (algo, accuracy) in enumerate(ranking, 1):
            metrics = evaluations[algo]
            self.stdout.write(f'\n#{i}: {algo.upper()}')
            self.stdout.write(f'  Accuracy:    {accuracy*100:.1f}%')
            self.stdout.write(f'  Hit Rate:    {metrics["hit_rate"]*100:.1f}%')
            self.stdout.write(f'  Precision:   {metrics["precision"]:.4f}')
            self.stdout.write(f'  Recall:      {metrics["recall"]:.4f}')
            self.stdout.write(f'  MRR:         {metrics["mrr"]:.4f}')
            self.stdout.write(f'  NDCG:        {metrics["ndcg"]:.4f}')
        
        # Summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('No single algorithm is labeled the winner.'))
        self.stdout.write(self.style.SUCCESS('Hybrid remains the selected production model while other methods are kept for comparison.'))

        report = ComparisonReport.objects.create(
            title=f'Algorithm Comparison - {timezone.now().strftime("%Y-%m-%d %H:%M")}',
            description='Comprehensive accuracy evaluation',
            metrics_data={k: {mk: float(mv) for mk, mv in v.items()} for k, v in evaluations.items()},
            ranking=[{'algorithm': algo, 'score': float(score)} for algo, score in ranking],
            winner=ranking[0][0],
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            is_final=True,
        )

        self.stdout.write(self.style.SUCCESS(f'Report saved: {report.title}\n'))
