from django.shortcuts import render
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from .services import RecommendationService
from .models import RecommendationEvent, UserInteraction
from products.models import Product
import json


def get_user_recommendations(request):
    """Get recommendations for user via API."""
    algorithm = request.GET.get('algorithm', 'hybrid')
    limit = int(request.GET.get('limit', 8))
    
    service = RecommendationService()
    
    if request.user.is_authenticated:
        products = service.get_recommendations_for_user(
            request.user, algorithm=algorithm, limit=limit
        )
    else:
        products = Product.objects.filter(
            is_available=True, is_active=True
        ).order_by('-views_count')[:limit]
    
    # Track impressions
    if request.user.is_authenticated or request.session.session_key:
        for i, product in enumerate(products):
            RecommendationEvent.track_event(
                user=request.user if request.user.is_authenticated else None,
                session_key=request.session.session_key,
                algorithm=algorithm,
                event_type='impression',
                product=product,
                position=i + 1
            )
    
    if request.htmx:
        return render(request, 'recommendations/partials/recommendation_grid.html', {
            'products': products,
            'algorithm': algorithm,
        })
    
    return JsonResponse({
        'products': [{
            'id': p.id,
            'name': p.name,
            'price': str(p.price),
            'image': p.image.url if p.image else None,
            'url': p.get_absolute_url(),
        } for p in products],
        'algorithm': algorithm,
        'count': len(products),
    })


def get_product_recommendations(request, product_id):
    """Get recommendations based on a specific product."""
    algorithm = request.GET.get('algorithm', 'item_based_cf')
    limit = int(request.GET.get('limit', 6))
    
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    
    service = RecommendationService()
    products = service.get_similar_products(product, algorithm=algorithm, limit=limit)
    
    return JsonResponse({
        'products': [{
            'id': p.id,
            'name': p.name,
            'price': str(p.price),
            'image': p.image.url if p.image else None,
            'url': p.get_absolute_url(),
        } for p in products],
        'algorithm': algorithm,
    })


@login_required
@require_http_methods(["POST"])
def track_recommendation_click(request):
    """Track when user clicks on a recommendation."""
    data = json.loads(request.body)
    
    try:
        product = Product.objects.get(id=data.get('product_id'))
        event = RecommendationEvent.track_event(
            user=request.user,
            session_key=request.session.session_key,
            algorithm=data.get('algorithm', 'hybrid'),
            event_type='click',
            product=product,
            position=int(data.get('position', 0))
        )
        
        # Also track as interaction
        UserInteraction.track_interaction(
            user=request.user,
            product=product,
            interaction_type='click',
            algorithm_used=data.get('algorithm')
        )
        
        return JsonResponse({'status': 'success'})
    except Product.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Product not found'}, status=404)


@login_required
def compare_algorithms(request):
    """Compare all algorithms side by side."""
    service = RecommendationService()
    results = service.compare_all_algorithms(request.user)
    
    return render(request, 'recommendations/compare.html', {
        'results': results,
    })
