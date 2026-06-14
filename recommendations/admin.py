from django.contrib import admin
from .models import RecommendationEvent, UserInteraction


@admin.register(RecommendationEvent)
class RecommendationEventAdmin(admin.ModelAdmin):
    list_display = ('algorithm', 'event_type', 'product', 'position', 'user', 'created_at')
    list_filter = ('algorithm', 'event_type', 'created_at')
    search_fields = ('product__name', 'user__email')


@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    list_display = ('user', 'interaction_type', 'product', 'target_product', 'weight', 'created_at')
    list_filter = ('interaction_type', 'created_at')
    search_fields = ('user__email', 'product__name')
