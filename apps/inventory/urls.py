from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_dashboard, name='dashboard'),

    # Supplier URLs
    path('suppliers/', views.supplier_list, name='supplier_list'),
    path('suppliers/create/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/update/', views.supplier_update, name='supplier_update'),
    path('suppliers/<int:pk>/', views.supplier_detail, name='supplier_detail'),

    # Material Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', views.category_update, name='category_update'),

    # Raw Material URLs
    path('materials/', views.material_list, name='material_list'),
    path('materials/create/', views.material_create, name='material_create'),
    path('materials/<int:pk>/', views.material_detail, name='material_detail'),  # Added detail view
    path('materials/<int:pk>/update/', views.material_update, name='material_update'),

    # Purchase Order URLs
    path('purchase-orders/', views.purchase_order_list, name='purchase_order_list'),
    path('purchase-orders/create/', views.purchase_order_create, name='purchase_order_create'),
    path('purchase-orders/<int:pk>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('purchase-orders/<int:pk>/update/', views.purchase_order_update, name='purchase_order_update'),
    path('purchase-orders/<int:pk>/delete/', views.purchase_order_delete, name='purchase_order_delete'),

    # Stock Receipt URLs
    path('receipts/', views.stock_receipt_list, name='stock_receipt_list'),
    path('receipts/create/', views.stock_receipt_create, name='stock_receipt_create'),
    path('receipts/<int:pk>/', views.stock_receipt_detail, name='stock_receipt_detail'),

    # Stock Adjustment URLs
    path('adjustments/', views.stock_adjustment_list, name='stock_adjustment_list'),
    path('adjustments/create/', views.stock_adjustment_create, name='stock_adjustment_create'),
    path('adjustments/<int:pk>/', views.stock_adjustment_detail, name='stock_adjustment_detail'),

    # Stock Movement URLs
    path('movements/', views.stock_movement_list, name='stock_movement_list'),
     path('movements/create/', views.stock_movement_create, name='stock_movement_create'),
    path('movements/<int:pk>/', views.stock_movement_detail, name='stock_movement_detail'),
    path('movements/update/<int:pk>/', views.stock_movement_update, name='stock_movement_update'),
    path('movements/delete/<int:pk>/', views.stock_movement_delete, name='stock_movement_delete'),
]