from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = 'accounts'

urlpatterns = [
    # Authentication URLs
    path('', views.dashboard_view, name='dashboard'),  # Dashboard URL
    path('login/', views.user_login, name='login'),
    path('logout/', LogoutView.as_view(), name='logout'), 
    path('password/reset/', views.password_reset, name='password_reset'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),  # Profile edit URL
    path('settings/', views.settings_view, name='settings'),  # Add settings URL
    path('profile/', views.profile_view, name='profile'),
    path('password/change/', views.password_change, name='password_change'),

    # Employee URLs
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/create/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/update/', views.employee_update, name='employee_update'),
    path('employees/<int:pk>/terminate/', views.employee_terminate, name='employee_terminate'),

    # Department urls 
    path('departments/', views.department_list, name='department_list'),
    path('departments/create/', views.department_create, name='department_create'),
    path('departments/update/<int:pk>/', views.department_update, name='department_update'),
    path('departments/delete/<int:pk>/', views.department_delete, name='department_delete'),
    
    # Document URLs
    path('employees/<int:employee_pk>/documents/upload/', views.document_upload, name='document_upload'),
    
    # Leave URLs
    path('leave/request/', views.leave_request, name='leave_request'),
    path('leave/<int:pk>/approve/', views.leave_approval, name='leave_approval'),
    path('leaves/', views.leave_list, name='leave_list'),  # Add the leave list URL

    # Attendance URLs
    path('attendance/upload/', views.attendance_upload, name='attendance_upload'),
    path('attendance/', views.attendance_list, name='attendance_list'),
]