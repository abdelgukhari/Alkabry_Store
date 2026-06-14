from .cart import CartHandler


def cart(request):
    """Make cart available in all templates."""
    return {'cart': CartHandler(request)}
