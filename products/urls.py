from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('manage/', views.product_manage_view, name='manage'),
    path('manage/create/', views.product_create_view, name='create'),
    path('products/', views.product_list_view, name='list'),
    path('products/<slug:slug>/edit/', views.product_edit_view, name='edit'),
    path('products/<slug:slug>/', views.product_detail_view, name='detail'),
    path('products/<slug:slug>/review/', views.add_review_view, name='add_review'),
    path('category/<slug:slug>/', views.category_view, name='category'),
    path('search/', views.search_view, name='search'),
    path('ajax/search/', views.ajax_search_view, name='ajax_search'),
]
