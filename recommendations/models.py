from django.db import models
from django.conf import settings
from products.models import Product

# Shared algorithm choices
ALGORITHM_CHOICES = [
    ('content_based', 'Content-Based Filtering'),
    ('user_based_cf', 'User-Based Collaborative Filtering'),
    ('item_based_cf', 'Item-Based Collaborative Filtering'),
    ('svd', 'SVD Matrix Factorization'),
    ('hybrid', 'Hybrid Recommendation System'),
]


class RecommendationEvent(models.Model):
    """Track recommendation events for algorithm comparison."""
    
    EVENT_TYPE_CHOICES = [
        ('impression', 'Impression'),
        ('click', 'Click'),
        ('add_to_cart', 'Add to Cart'),
        ('purchase', 'Purchase'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='recommendation_events'
    )
    session_key = models.CharField(max_length=100, blank=True, null=True)
    
    # Algorithm info
    algorithm = models.CharField(max_length=20, choices=ALGORITHM_CHOICES)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    
    # Product recommended
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='recommendation_events'
    )
    
    # Position in recommendation list (1-based)
    position = models.PositiveIntegerField()
    
    # Revenue generated (for purchases)
    revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0, null=True, blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'recommendation_events'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['algorithm', 'event_type']),
            models.Index(fields=['algorithm', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.algorithm} - {self.event_type} - {self.product.name}"
    
    @classmethod
    def track_event(cls, user=None, session_key=None, algorithm='hybrid', 
                   event_type='impression', product=None, position=0, revenue=None):
        """Track a recommendation event."""
        return cls.objects.create(
            user=user,
            session_key=session_key,
            algorithm=algorithm,
            event_type=event_type,
            product=product,
            position=position,
            revenue=revenue
        )


class UserInteraction(models.Model):
    """Track user interactions for recommendation training."""
    
    INTERACTION_TYPE_CHOICES = [
        ('view', 'Product View'),
        ('click', 'Recommendation Click'),
        ('add_to_cart', 'Add to Cart'),
        ('purchase', 'Purchase'),
        ('review', 'Review'),
        ('wishlist', 'Wishlist'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='interactions'
    )
    session_key = models.CharField(max_length=100, blank=True, null=True)
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='user_interactions'
    )
    target_product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='target_interactions',
        help_text='For recommendation clicks, the product that was recommended'
    )
    
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPE_CHOICES)
    weight = models.FloatField(default=1.0, help_text='Interaction weight for algorithms')
    
    # Additional context
    algorithm_used = models.CharField(
        max_length=20,
        choices=ALGORITHM_CHOICES,
        null=True,
        blank=True,
        help_text='Which algorithm led to this interaction (if applicable)'
    )
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_interactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'interaction_type']),
            models.Index(fields=['product', 'interaction_type']),
        ]
    
    def __str__(self):
        user_str = self.user.email if self.user else 'Anonymous'
        return f"{user_str} - {self.interaction_type} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Auto-set weight based on interaction type
        weight_map = {
            'view': 1.0,
            'click': 2.0,
            'add_to_cart': 3.0,
            'purchase': 5.0,
            'review': 4.0,
            'wishlist': 2.5,
        }
        if not self.weight:
            self.weight = weight_map.get(self.interaction_type, 1.0)
        super().save(*args, **kwargs)
    
    @classmethod
    def track_interaction(cls, user=None, session_key=None, product=None,
                         target_product=None, interaction_type='view', 
                         algorithm_used=None, weight=None):
        """Track a user interaction."""
        return cls.objects.create(
            user=user,
            session_key=session_key,
            product=product,
            target_product=target_product,
            interaction_type=interaction_type,
            algorithm_used=algorithm_used,
            weight=weight
        )
