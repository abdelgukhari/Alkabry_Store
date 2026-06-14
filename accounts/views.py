from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm
from orders.models import Order
from products.models import Product
from recommendations.services import RecommendationService
from recommendations.models import RecommendationEvent


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            user = authenticate(email=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('accounts:dashboard')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('products:home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully! Please login.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('products:home')


@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})


@login_required
@require_http_methods(["POST"])
def update_profile_view(request):
    form = UserProfileForm(request.POST, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully!')
    else:
        messages.error(request, 'Error updating profile.')
    return redirect('accounts:profile')


@login_required
def order_history_view(request):
    orders = request.user.orders.all()
    return render(request, 'accounts/order_history.html', {'orders': orders})


@login_required
def user_dashboard_view(request):
    """Amazon-style user dashboard with orders, recommendations, and account overview."""
    # Recent orders
    recent_orders = request.user.orders.all().order_by('-created_at')[:5]

    # Order stats
    total_orders = request.user.orders.count()
    total_spent = request.user.orders.aggregate(
        total=Sum('total')
    )['total'] or 0
    pending_orders = request.user.orders.filter(status__in=['pending', 'processing']).count()

    # Recommendations
    service = RecommendationService()
    recommended_products = service.get_recommendations_for_user(
        request.user, algorithm='hybrid', limit=8
    )

    # Recently viewed (from interactions)
    from recommendations.models import UserInteraction
    recent_interactions = UserInteraction.objects.filter(
        user=request.user,
        interaction_type='view'
    ).select_related('product').order_by('-created_at')[:6]
    recently_viewed_products = [interaction.product for interaction in recent_interactions if interaction.product]

    # Wishlist-like: most interacted products
    top_products = Product.objects.filter(
        user_interactions__user=request.user
    ).annotate(
        interaction_count=Count('user_interactions')
    ).order_by('-interaction_count')[:4]

    context = {
        'recent_orders': recent_orders,
        'total_orders': total_orders,
        'total_spent': float(total_spent),
        'pending_orders': pending_orders,
        'recommended_products': recommended_products,
        'recently_viewed': recently_viewed_products,
        'top_products': top_products,
    }
    return render(request, 'accounts/dashboard.html', context)


@staff_member_required
def admin_dashboard_view(request):
    """Admin-only dashboard with full analytics, algorithm comparison, and reports."""
    # Get date range
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)

    # Algorithm performance
    algorithm_stats = {}
    for algo in RecommendationService.ALGORITHMS:
        events = RecommendationEvent.objects.filter(
            algorithm=algo,
            created_at__gte=start_date
        )

        impressions = events.filter(event_type='impression').count()
        clicks = events.filter(event_type='click').count()
        add_to_carts = events.filter(event_type='add_to_cart').count()
        purchases = events.filter(event_type='purchase').count()

        revenue = events.filter(
            event_type='purchase'
        ).aggregate(total=Sum('revenue'))['total'] or 0

        algorithm_stats[algo] = {
            'impressions': impressions,
            'clicks': clicks,
            'add_to_carts': add_to_carts,
            'purchases': purchases,
            'revenue': float(revenue),
            'ctr': (clicks / impressions * 100) if impressions > 0 else 0,
            'conversion_rate': (purchases / impressions * 100) if impressions > 0 else 0,
        }

    # Overall stats
    total_orders = Order.objects.filter(created_at__gte=start_date).count()
    total_revenue = Order.objects.filter(
        created_at__gte=start_date
    ).aggregate(total=Sum('total'))['total'] or 0
    from accounts.models import User
    total_users = User.objects.count()
    total_products = Product.objects.filter(is_active=True, is_available=True).count()

    # Top products
    top_products = Product.objects.order_by('-purchases_count')[:10]

    # Chart data
    chart_data = {
        'labels': list(algorithm_stats.keys()),
        'ctr': [stats['ctr'] for stats in algorithm_stats.values()],
        'conversion_rate': [stats['conversion_rate'] for stats in algorithm_stats.values()],
        'revenue': [stats['revenue'] for stats in algorithm_stats.values()],
        'purchases': [stats['purchases'] for stats in algorithm_stats.values()],
    }

    # Algorithm evaluation scores (cached, skip if too slow)
    evaluations = {}
    try:
        service = RecommendationService()
        # Only evaluate 2 fastest algorithms for dashboard
        for algo in ['item_based_cf', 'hybrid']:
            metrics = service.evaluate_algorithm(algo)
            if metrics:
                evaluations[algo] = metrics
    except Exception:
        pass  # Skip evaluation if it fails or is too slow

    context = {
        'algorithm_stats': algorithm_stats,
        'total_orders': total_orders,
        'total_revenue': float(total_revenue),
        'total_users': total_users,
        'total_products': total_products,
        'top_products': top_products,
        'chart_data': chart_data,
        'days': days,
        'evaluations': evaluations,
        'metric_names': ['precision', 'recall', 'f1_score', 'ndcg', 'hit_rate', 'mrr', 'accuracy'],
    }
    return render(request, 'admin_dashboard.html', context)
