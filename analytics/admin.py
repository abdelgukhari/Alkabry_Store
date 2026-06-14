from django.contrib import admin
from .models import AlgorithmMetrics, ComparisonReport


@admin.register(AlgorithmMetrics)
class AlgorithmMetricsAdmin(admin.ModelAdmin):
    list_display = ('algorithm', 'date', 'impressions', 'clicks', 'purchases', 'ctr', 'total_revenue')
    list_filter = ('algorithm', 'date')


@admin.register(ComparisonReport)
class ComparisonReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'winner', 'start_date', 'end_date', 'is_final', 'created_at')
    list_filter = ('is_final',)
    search_fields = ('title', 'description')
