from django.urls import path
from . import views

app_name = 'products'  # Correct app name

urlpatterns = [
    # Product Dashboard URL
    path('dashboard/', views.product_dashboard, name='dashboard'),

    # Product Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'), 
    
    # Product URLs
    path('', views.product_list, name='product_list'),
    path('report/', views.product_report, name='product_report'),
    path('create/', views.product_create, name='product_create'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('<int:pk>/update/', views.product_update, name='product_update'),
    path('product/<int:product_id>/selling-price-report/', views.product_selling_price_report, name='product_selling_price_report'),
    
    # Product Formula URLs
    path('products/<int:product_id>/formulas/create/', views.formula_create, name='formula_create'),
    path('formulas/<int:pk>/update/', views.formula_update, name='formula_update'),
    path('formula/<int:pk>/delete/', views.formula_delete, name='formula_delete'),
    path('product/<int:product_id>/formulas/', views.formula_list, name='formula_list'),

    
    # Product Movement URLs
    path('movements/', views.product_movement_list, name='product_movement_list'),
    path('movements/create/', views.product_movement_create, name='product_movement_create'),
    path('movements/update/<int:pk>/', views.product_movement_update, name='product_movement_update'),
    path('movements/delete/<int:pk>/', views.product_movement_delete, name='product_movement_delete'),
]