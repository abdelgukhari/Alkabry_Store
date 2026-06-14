from .models import Category


def nav_categories(request):
    """Provide top-level categories to every template for the navbar."""
    return {
        'nav_categories': Category.objects.filter(
            parent=None, is_active=True
        ).order_by('name'),
    }
