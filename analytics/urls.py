from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('api/algorithm-performance/', views.algorithm_performance_api, name='api_performance'),
    path('compare/', views.compare_view, name='compare'),
    path('generate-report/', views.generate_report_view, name='generate_report'),
]
