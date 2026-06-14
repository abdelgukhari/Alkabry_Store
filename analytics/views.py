import json
from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from .models import AlgorithmMetrics, ComparisonReport
from recommendations.services import RecommendationService
from recommendations.models import RecommendationEvent
from products.models import Product
from orders.models import Order


@staff_member_required
def dashboard_view(request):
    """Analytics dashboard with algorithm stats and charts."""
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)

    algorithm_stats = {}
    for algo in RecommendationService.ALGORITHMS:
        events = RecommendationEvent.objects.filter(
            algorithm=algo,
            created_at__gte=start_date
        )
        impressions = events.filter(event_type='impression').count()
        clicks = events.filter(event_type='click').count()
        purchases = events.filter(event_type='purchase').count()
        revenue = events.filter(
            event_type='purchase'
        ).aggregate(total=Sum('revenue'))['total'] or 0

        algorithm_stats[algo] = {
            'impressions': impressions,
            'clicks': clicks,
            'purchases': purchases,
            'revenue': float(revenue),
            'ctr': (clicks / impressions * 100) if impressions > 0 else 0,
            'conversion_rate': (purchases / impressions * 100) if impressions > 0 else 0,
        }

    total_orders = Order.objects.filter(created_at__gte=start_date).count()
    total_revenue = Order.objects.filter(
        created_at__gte=start_date
    ).aggregate(total=Sum('total'))['total'] or 0
    top_products = Product.objects.order_by('-purchases_count')[:10]

    chart_data = {
        'labels': list(algorithm_stats.keys()),
        'ctr': [stats['ctr'] for stats in algorithm_stats.values()],
        'conversion_rate': [stats['conversion_rate'] for stats in algorithm_stats.values()],
        'revenue': [stats['revenue'] for stats in algorithm_stats.values()],
    }

    context = {
        'algorithm_stats': algorithm_stats,
        'total_orders': total_orders,
        'total_revenue': float(total_revenue),
        'top_products': top_products,
        'chart_data': chart_data,
        'days': days,
    }
    return render(request, 'analytics/dashboard.html', context)


@staff_member_required
def algorithm_performance_api(request):
    """API endpoint for algorithm performance data."""
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)

    data = {}
    for algo in RecommendationService.ALGORITHMS:
        metrics = AlgorithmMetrics.objects.filter(
            algorithm=algo,
            date__gte=start_date
        ).aggregate(
            avg_precision=Avg('precision'),
            avg_recall=Avg('recall'),
            avg_f1=Avg('f1_score'),
            avg_ndcg=Avg('ndcg'),
            avg_diversity=Avg('diversity'),
            avg_coverage=Avg('coverage'),
        )

        data[algo] = metrics

    return JsonResponse(data)


@staff_member_required
def compare_view(request):
    """Compare all algorithms side by side."""
    preferred_algorithm = 'hybrid'

    # Get evaluation metrics for each algorithm with Hybrid as first section.
    evaluations = {}
    algorithm_order = [preferred_algorithm] + [algo for algo in RecommendationService.ALGORITHMS if algo != preferred_algorithm]
    for algo in algorithm_order:
        row = AlgorithmMetrics.objects.filter(
            algorithm=algo
        ).order_by('-date').first()

        if row:
            hit_rate = float(row.hit_rate) if row.hit_rate else 1.0
            ndcg = float(row.ndcg)
            precision = float(row.precision)
            recall = float(row.recall)
            f1 = float(row.f1_score)
            accuracy = hit_rate * 0.50 + ndcg * 0.30 + precision * 0.20
            evaluations[algo] = {
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'ndcg': ndcg,
                'hit_rate': hit_rate,
                'accuracy': accuracy,
                'mrr': 0.0,
            }

    # Get historical performance
    historical_data = {}
    for algo in RecommendationService.ALGORITHMS:
        metrics = AlgorithmMetrics.objects.filter(
            algorithm=algo
        ).order_by('-date')[:30]

        historical_data[algo] = {
            'ctr': [(m.date.strftime('%Y-%m-%d'), m.ctr * 100) for m in metrics],
            'conversion_rate': [(m.date.strftime('%Y-%m-%d'), m.conversion_rate * 100) for m in metrics],
            'revenue': [(m.date.strftime('%Y-%m-%d'), float(m.total_revenue)) for m in metrics],
        }

    # Accuracy = HR@10×0.50 + NDCG×0.30 + Precision×0.20  (thesis formula)
    scores = {}
    if evaluations:
        for algo, metrics in evaluations.items():
            scores[algo] = metrics.get('accuracy',
                metrics.get('hit_rate', 1.0) * 0.50 +
                metrics.get('ndcg', 0) * 0.30 +
                metrics.get('precision', 0) * 0.20
            )

    context = {
        'evaluations': evaluations,
        'evaluations_json': json.dumps(evaluations),
        'historical_data': historical_data,
        'scores': scores,
        'preferred_algorithm': preferred_algorithm,
    }
    return render(request, 'analytics/compare.html', context)


@staff_member_required
def generate_report_view(request):
    """Generate a comparison report using the latest saved benchmark metrics."""
    # Read from DB (populated by generate_benchmark_data) — consistent with terminal output.
    evaluations = {}
    for algo in RecommendationService.ALGORITHMS:
        row = AlgorithmMetrics.objects.filter(algorithm=algo).order_by('-date').first()
        if row:
            hit_rate = float(row.hit_rate) if row.hit_rate else 1.0
            ndcg = float(row.ndcg)
            precision = float(row.precision)
            recall = float(row.recall)
            evaluations[algo] = {
                'precision': precision,
                'recall': recall,
                'f1_score': float(row.f1_score),
                'ndcg': ndcg,
                'hit_rate': hit_rate,
                'mrr': 0.0,
                'accuracy': hit_rate * 0.50 + ndcg * 0.30 + precision * 0.20,
            }

    # Accuracy = HR@10×0.50 + NDCG×0.30 + Precision×0.20  (thesis formula)
    scores = {}
    for algo, metrics in evaluations.items():
        scores[algo] = metrics['accuracy']

    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    winner = ranking[0][0] if ranking else None

    # Create report
    report = ComparisonReport.objects.create(
        title=f'Algorithm Comparison Report - {timezone.now().strftime("%Y-%m-%d")}',
        description='Comprehensive comparison of all recommendation algorithms',
        metrics_data=evaluations,
        ranking=[{'algorithm': algo, 'score': score} for algo, score in ranking],
        winner=winner,
        start_date=timezone.now() - timedelta(days=30),
        end_date=timezone.now(),
        is_final=True,
    )

    return render(request, 'analytics/report.html', {
        'report': report,
        'evaluations': evaluations,
        'ranking': ranking,
        'winner': winner,
    })
