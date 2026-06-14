from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('api/user/', views.get_user_recommendations, name='api_user'),
    path('api/product/<int:product_id>/', views.get_product_recommendations, name='api_product'),
    path('api/compare/', views.compare_algorithms, name='compare'),
    path('track/click/', views.track_recommendation_click, name='track_click'),
]
