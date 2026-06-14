from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    """Product category model with hierarchical support."""
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('products:category', args=[self.slug])
    
    @property
    def product_count(self):
        return self.products.count()


class Tag(models.Model):
    """Product tags for content-based filtering."""
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    
    class Meta:
        db_table = 'tags'
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(models.Model):
    """Product model with all attributes for recommendations."""
    
    name = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=255, blank=True)
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Original price for showing discounts'
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # Inventory
    sku = models.CharField(max_length=100, unique=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    
    # Categorization
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='products')
    
    # Product attributes for content-based filtering
    brand = models.CharField(max_length=100, blank=True)
    color = models.CharField(max_length=50, blank=True)
    size = models.CharField(max_length=50, blank=True)
    material = models.CharField(max_length=100, blank=True)
    
    # Media
    image = models.ImageField(upload_to='products/', blank=True)
    
    # Ratings (cached for performance)
    avg_rating = models.FloatField(default=0.0)
    rating_count = models.PositiveIntegerField(default=0)
    
    # Analytics
    views_count = models.PositiveIntegerField(default=0)
    purchases_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category']),
            models.Index(fields=['is_available', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.short_description and self.description:
            self.short_description = self.description[:200] + '...'
        if not self.sku:
            import uuid
            self.sku = f'SKU-{uuid.uuid4().hex[:8].upper()}'
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('products:detail', args=[self.slug])
    
    @property
    def discount_percentage(self):
        if self.compare_price and self.compare_price > self.price:
            return int(((self.compare_price - self.price) / self.compare_price) * 100)
        return 0
    
    @property
    def is_in_stock(self):
        return self.stock > 0 and self.is_available
    
    def update_rating(self):
        """Update cached rating from reviews."""
        reviews = self.reviews.filter(is_approved=True)
        self.avg_rating = reviews.aggregate(
            models.Avg('rating')
        )['rating__avg'] or 0.0
        self.rating_count = reviews.count()
        self.save(update_fields=['avg_rating', 'rating_count'])


class ProductImage(models.Model):
    """Additional product images."""
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(upload_to='products/gallery/')
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_images'
    
    def __str__(self):
        return f"Image for {self.product.name}"


class Review(models.Model):
    """Product reviews and ratings - crucial for collaborative filtering."""
    
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    rating = models.IntegerField(choices=RATING_CHOICES)
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reviews'
        unique_together = ['product', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Review by {self.user.email} for {self.product.name}"
