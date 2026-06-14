from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from products.models import Product
from .cart import CartHandler


def cart_detail_view(request):
    """View cart contents."""
    cart = CartHandler(request)
    return render(request, 'cart/detail.html', {'cart': cart})


@require_http_methods(["POST"])
def cart_add_view(request):
    """Add product to cart."""
    cart = CartHandler(request)
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    
    product = get_object_or_404(Product, id=product_id, is_available=True)
    
    if product.stock < quantity:
        messages.error(request, f'Only {product.stock} items in stock.')
        if request.htmx:
            return render(request, 'cart/partials/messages.html', {
                'messages': messages.get_messages(request)
            })
        return redirect('products:detail', slug=product.slug)
    
    cart.add(product, quantity=quantity)
    messages.success(request, f'{product.name} added to cart!')
    
    # Track interaction
    from recommendations.models import UserInteraction
    user = request.user if request.user.is_authenticated else None
    UserInteraction.track_interaction(
        user=user,
        session_key=request.session.session_key,
        product=product,
        interaction_type='add_to_cart'
    )
    
    if request.htmx:
        return render(request, 'cart/partials/cart_count.html')
    
    return redirect('cart:detail')


@require_http_methods(["POST"])
def cart_remove_view(request, item_id):
    """Remove product from cart."""
    cart = CartHandler(request)
    try:
        item = cart.items.get(id=item_id)
        product = item.product
        cart.remove(product)
        messages.success(request, f'{product.name} removed from cart.')
    except Exception:
        messages.error(request, 'Error removing item from cart.')
    
    if request.htmx:
        return render(request, 'cart/partials/cart_items.html', {'cart': cart})
    
    return redirect('cart:detail')


@require_http_methods(["POST"])
def cart_update_view(request, item_id):
    """Update product quantity in cart."""
    quantity = int(request.POST.get('quantity', 1))
    cart = CartHandler(request)
    
    try:
        item = cart.items.get(id=item_id)
        product = item.product
        
        if quantity <= 0:
            cart.remove(product)
            messages.success(request, f'{product.name} removed from cart.')
        else:
            if product.stock < quantity:
                messages.error(request, f'Only {product.stock} items in stock.')
                quantity = product.stock
            
            cart.update(product, quantity)
            messages.success(request, 'Cart updated.')
    except Exception:
        messages.error(request, 'Error updating cart.')
    
    if request.htmx:
        return render(request, 'cart/partials/cart_items.html', {'cart': cart})
    
    return redirect('cart:detail')


@require_http_methods(["POST"])
def cart_clear_view(request):
    """Clear the cart."""
    cart = CartHandler(request)
    cart.clear()
    messages.success(request, 'Cart cleared.')
    
    if request.htmx:
        return render(request, 'cart/partials/cart_items.html', {'cart': CartHandler(request)})
    
    return redirect('cart:detail')
