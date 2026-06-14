from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from cart.cart import CartHandler
from .models import Order, OrderItem
from .forms import CheckoutForm


@login_required
def checkout_view(request):
    """Checkout page with complete order placement."""
    cart = CartHandler(request)

    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty.')
        return redirect('products:home')

    if request.method == 'POST':
        form = CheckoutForm(request.POST, instance=request.user)
        if form.is_valid():
            # Save user profile info
            form.save()

            # Get shipping info from form
            shipping_info = {
                'address': form.cleaned_data.get('address'),
                'city': form.cleaned_data.get('city'),
                'country': form.cleaned_data.get('country'),
                'zip_code': form.cleaned_data.get('zip_code'),
                'phone': form.cleaned_data.get('phone'),
            }

            # Validate stock availability
            for item in cart.items:
                if item.product.stock < item.quantity:
                    messages.error(
                        request,
                        f'Only {item.product.stock} units of "{item.product.name}" available. '
                        f'Please update your cart.'
                    )
                    return redirect('cart:detail')

            # Create order atomically
            try:
                with transaction.atomic():
                    # Create order
                    order = Order.objects.create(
                        user=request.user,
                        shipping_address=shipping_info['address'],
                        shipping_city=shipping_info['city'],
                        shipping_country=shipping_info['country'],
                        shipping_zip_code=shipping_info['zip_code'],
                        shipping_phone=shipping_info['phone'],
                        payment_method='cash_on_delivery',
                        status='pending',
                        notes=request.POST.get('notes', ''),
                    )

                    # Create order items and update stock
                    for item in cart.items:
                        OrderItem.objects.create(
                            order=order,
                            product=item.product,
                            product_name=item.product.name,
                            product_sku=item.product.sku,
                            price=item.product.price,
                            quantity=item.quantity,
                        )

                        # Reduce stock
                        item.product.stock -= item.quantity
                        item.product.purchases_count += item.quantity
                        item.product.save(update_fields=['stock', 'purchases_count'])

                        # Track purchase interaction
                        from recommendations.models import UserInteraction
                        UserInteraction.track_interaction(
                            user=request.user,
                            product=item.product,
                            interaction_type='purchase'
                        )

                    # Calculate totals
                    order.calculate_totals()
                    order.status = 'processing'
                    order.save(update_fields=['status', 'subtotal', 'total'])

                    # Clear cart
                    cart.clear()

                messages.success(
                    request,
                    f'Order {order.order_number} placed successfully! '
                    f'Total: ${order.total}'
                )
                return redirect('orders:success', order_number=order.order_number)

            except Exception as e:
                messages.error(request, f'Error placing order: {str(e)}')
                return redirect('orders:checkout')
    else:
        form = CheckoutForm(instance=request.user)

    context = {
        'form': form,
        'cart': cart,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def order_success_view(request, order_number):
    """Order success page."""
    try:
        order = Order.objects.get(order_number=order_number, user=request.user)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('products:home')
    
    return render(request, 'orders/success.html', {'order': order})
