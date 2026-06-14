from django.db import models


class AlgorithmMetrics(models.Model):
    """Aggregate metrics for recommendation algorithm comparison."""
    
    ALGORITHM_CHOICES = [
        ('content_based', 'Content-Based Filtering'),
        ('user_based_cf', 'User-Based Collaborative Filtering'),
        ('item_based_cf', 'Item-Based Collaborative Filtering'),
        ('svd', 'SVD Matrix Factorization'),
        ('hybrid', 'Hybrid Recommendation System'),
    ]
    
    algorithm = models.CharField(max_length=20, choices=ALGORITHM_CHOICES)
    date = models.DateField()
    
    # Impression metrics
    impressions = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    add_to_carts = models.PositiveIntegerField(default=0)
    purchases = models.PositiveIntegerField(default=0)
    
    # Calculated rates
    ctr = models.FloatField(default=0.0, help_text='Click-through rate')
    conversion_rate = models.FloatField(default=0.0, help_text='Conversion rate')
    
    # Revenue
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    avg_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Quality metrics (computed by evaluation script)
    precision = models.FloatField(default=0.0, null=True, blank=True)
    recall = models.FloatField(default=0.0, null=True, blank=True)
    f1_score = models.FloatField(default=0.0, null=True, blank=True)
    ndcg = models.FloatField(default=0.0, null=True, blank=True)
    hit_rate = models.FloatField(default=0.0, null=True, blank=True)
    diversity = models.FloatField(default=0.0, null=True, blank=True)
    coverage = models.FloatField(default=0.0, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'algorithm_metrics'
        unique_together = ['algorithm', 'date']
        ordering = ['-date', 'algorithm']
    
    def __str__(self):
        return f"{self.algorithm} - {self.date}"
    
    def save(self, *args, **kwargs):
        # Calculate rates
        if self.impressions > 0:
            self.ctr = self.clicks / self.impressions
            self.conversion_rate = self.purchases / self.impressions
        if self.purchases > 0:
            self.avg_order_value = self.total_revenue / self.purchases
        super().save(*args, **kwargs)


class ComparisonReport(models.Model):
    """Store comparison reports between algorithms."""
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Report data (stored as JSON for flexibility)
    metrics_data = models.JSONField(help_text='Aggregated metrics for all algorithms')
    ranking = models.JSONField(help_text='Algorithm ranking based on metrics')
    winner = models.CharField(max_length=20, help_text='Best performing algorithm')
    
    # Time period
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    is_final = models.BooleanField(default=False, help_text='Mark as final comparison')
    
    class Meta:
        db_table = 'comparison_reports'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
