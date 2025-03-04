from django.urls import path
from . import views

app_name = 'production'

urlpatterns = [
    # Production Line URLs
    path('', views.production_dashboard_view, name='dashboard'),  # Production dashboard URL
    path('lines/', views.production_line_list, name='production_line_list'),
    path('lines/create/', views.production_line_create, name='production_line_create'),
    path('lines/<int:pk>/', views.production_line_detail, name='production_line_detail'),
    path('lines/<int:pk>/update/', views.production_line_update, name='production_line_update'),
    
    # Production Schedule URLs
    path('schedule/create/', views.schedule_create, name='schedule_create'),
    path('schedules/', views.schedule_list, name='schedule_list'),  
    path('schedule/create/<int:line_pk>/', views.schedule_create, name='schedule_create_for_line'),
    path('schedule/<int:pk>/', views.schedule_detail, name='schedule_detail'),
    
    # Production Batch URLs
    path('batch/create/<int:schedule_pk>/', views.batch_create, name='batch_create'),
    path('batch/<int:pk>/', views.batch_detail, name='batch_detail'),
    path('batch/<int:pk>/update/', views.batch_update, name='batch_update'),
    
    # Adding new paths for materials and employee costs
    path('batch/<int:batch_pk>/add-materials/', views.add_materials_to_batch, name='add_materials_to_batch'),
    path('batch/<int:batch_pk>/add-employee-costs/', views.add_employee_costs_to_batch, name='add_employee_costs_to_batch'),

    # Update Material Usage URLs
    path('batch/<int:batch_pk>/material-usage/<int:usage_pk>/update/', views.material_usage_update, name='material_usage_update'),  
    path('batch/<int:batch_pk>/material-usage/delete/<int:pk>/', views.material_usage_delete, name='material_usage_delete'),

    # Update Employee Costs URLs
    path('batch/<int:batch_pk>/employee-costs/<int:cost_pk>/update/', views.employee_cost_update, name='employee_cost_update'),
    path('batch/<int:batch_pk>/employee-cost/delete/<int:pk>/', views.employee_cost_delete, name='employee_cost_delete'),
    
    # Quality Check URLs
    path('batch/<int:batch_pk>/quality-check/', views.quality_check_create, name='quality_check_create'),
    
    # Maintenance URLs
    path('lines/<int:line_pk>/maintenance/', views.maintenance_create, name='maintenance_create'),
    
    # Report URLs
    path('reports/', views.generate_production_report, name='generate_report'),
    
    # API URLs
    path('api/lines/<int:pk>/status/', views.production_line_status, name='line_status_api'),
]