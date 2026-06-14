from decimal import Decimal
from django.conf import settings
from products.models import Product
from .models import Cart as CartModel, CartItem


class CartHandler:
    """Cart handler - manages cart in session or database."""
    
    def __init__(self, request):
        self.request = request
        self.session = request.session
        
        # Try to get cart from session
        cart_id = self.session.get('cart_id')
        
        # If user is authenticated, use their cart
        if request.user.is_authenticated:
            self.cart, created = CartModel.objects.get_or_create(user=request.user)
        elif cart_id:
            try:
                self.cart = CartModel.objects.get(id=cart_id)
            except CartModel.DoesNotExist:
                self.cart = self._create_cart()
        else:
            self.cart = self._create_cart()
        
        # Save cart ID to session
        self.session['cart_id'] = self.cart.id
        self.session.modified = True
    
    def _create_cart(self):
        """Create a new cart."""
        if self.request.user.is_authenticated:
            return CartModel.objects.create(user=self.request.user)
        return CartModel.objects.create(session_key=self.session.session_key)
    
    def add(self, product, quantity=1, override_quantity=False):
        """Add product to cart."""
        cart_item, created = CartItem.objects.get_or_create(
            cart=self.cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created and override_quantity:
            cart_item.quantity = quantity
            cart_item.save()
        elif not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        self.session.modified = True
    
    def remove(self, product):
        """Remove product from cart."""
        try:
            item = CartItem.objects.get(cart=self.cart, product=product)
            item.delete()
            self.session.modified = True
        except CartItem.DoesNotExist:
            pass
    
    def update(self, product, quantity):
        """Update product quantity in cart."""
        try:
            item = CartItem.objects.get(cart=self.cart, product=product)
            if quantity > 0:
                item.quantity = quantity
                item.save()
            else:
                item.delete()
            self.session.modified = True
        except CartItem.DoesNotExist:
            pass
    
    def clear(self):
        """Clear the cart."""
        self.cart.items.all().delete()
        self.session.modified = True
    
    @property
    def items(self):
        """Get all cart items."""
        return self.cart.items.select_related('product').all()
    
    def __iter__(self):
        """Iterate over cart items."""
        for item in self.items:
            item.subtotal = item.subtotal
            yield item
    
    def __len__(self):
        """Get total items in cart."""
        return self.cart.total_items
    
    def get_total_price(self):
        """Get total price of cart."""
        return self.cart.total_price
    
    def save(self):
        """Save cart changes."""
        self.session.modified = True
