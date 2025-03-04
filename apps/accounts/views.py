from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm, PasswordResetForm
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from apps.production.models import EmployeeCost, ProductionBatch
from .models import *
from .forms import *
import csv
from datetime import datetime
from django.utils import timezone

# Dashboard view
@login_required
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html', {
        'title': 'Dashboard'
    })

# Settings view
def settings_view(request):
    user = request.user
    employee_profile = None
    superuser_profile = None
    admin_profile = None

    # Check if the user has an associated Employee profile
    if user.employee:
        employee_profile = user.employee

    # Check for superuser profile
    if hasattr(user, 'superuserprofile'):
        superuser_profile = user.superuserprofile

    # Check for admin profile
    if hasattr(user, 'adminprofile'):
        admin_profile = user.adminprofile

    context = {
        'user': user,
        'employee_profile': employee_profile,
        'superuser_profile': superuser_profile,
        'admin_profile': admin_profile,
    }

    return render(request, 'accounts/settings.html', context)
# Edit profile view

@login_required
def profile_edit(request):
    user = request.user
    employee_instance = None
    superuser_profile_instance = None
    admin_profile_instance = None

    # Check for the employee profile
    if hasattr(user, 'employee'):
        employee_instance = user.employee

    # Check for superuser profile
    if hasattr(user, 'superuserprofile'):
        superuser_profile_instance = user.superuserprofile

    # Check for admin profile
    if hasattr(user, 'adminprofile'):
        admin_profile_instance = user.adminprofile

    if request.method == 'POST':
        # Use the appropriate form based on the user role
        if superuser_profile_instance:
            profile_form = SuperUserProfileForm(request.POST, instance=superuser_profile_instance)
        elif admin_profile_instance:
            profile_form = AdminProfileForm(request.POST, instance=admin_profile_instance)
        else:
            profile_form = EmployeeForm(request.POST, instance=employee_instance)

        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        # Initialize the appropriate form based on the user role
        if superuser_profile_instance:
            profile_form = SuperUserProfileForm(instance=superuser_profile_instance)
        elif admin_profile_instance:
            profile_form = AdminProfileForm(instance=admin_profile_instance)
        else:
            profile_form = EmployeeForm(instance=employee_instance)

    return render(request, 'accounts/profile_edit.html', {
        'profile_form': profile_form,
        'title': 'Edit Profile'
    })


# User login view
def user_login(request):
    if request.method == 'POST':
        email = request.POST.get('username')  # Adjusted to use 'username' as per your form
        password = request.POST.get('password')
        
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in successfully.')
            return redirect('accounts:employee_list')  # Redirect to employee list or dashboard
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'accounts/auth/login.html')

# Password reset view
def password_reset(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(request=request)
            messages.success(request, 'Password reset email sent.')
            return redirect('accounts:user_login')
    else:
        form = PasswordResetForm()
    return render(request, 'accounts/auth/password_reset.html', {'form': form})

@login_required
@permission_required('accounts.view_employee')
def employee_list(request):
    search_query = request.GET.get('search', '')
    department_filter = request.GET.get('department', '')
    status_filter = request.GET.get('status', '')

    employees = Employee.objects.all()

    if search_query:
        employees = employees.filter(
            Q(employee_id__icontains=search_query) |
            Q(national_id__icontains=search_query)  # Adjusted to reflect no user field
        )

    if department_filter:
        employees = employees.filter(department_id=department_filter)

    if status_filter:
        employees = employees.filter(employment_status=status_filter)

    paginator = Paginator(employees, 20)
    page = request.GET.get('page')
    employees = paginator.get_page(page)

    departments = Department.objects.all()

    context = {
        'employees': employees,
        'departments': departments,
        'search_query': search_query,
        'department_filter': department_filter,
        'status_filter': status_filter,
    }
    return render(request, 'accounts/employee_list.html', context)


# Create Employee
@login_required
@permission_required('accounts.add_employee')
def employee_create(request):
    if request.method == 'POST':
        employee_form = EmployeeForm(request.POST)
        
        if employee_form.is_valid():
            employee = employee_form.save()  # Save the employee directly
            messages.success(request, 'Employee created successfully.')
            return redirect('accounts:employee_detail', pk=employee.pk)
    else:
        employee_form = EmployeeForm()

    return render(request, 'accounts/employee_form.html', {
        'employee_form': employee_form,
        'title': 'Create New Employee'
    })

@login_required
@permission_required('accounts.change_employee')
def employee_update(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        employee_form = EmployeeForm(request.POST, instance=employee)
        if employee_form.is_valid():
            employee_form.save()
            messages.success(request, 'Employee updated successfully.')
            return redirect('accounts:employee_detail', pk=employee.pk)
    else:
        employee_form = EmployeeForm(instance=employee)

    return render(request, 'accounts/employee_form.html', {
        'employee_form': employee_form,
        'employee': employee,
        'title': 'Update Employee'
    })

@login_required
@permission_required('accounts.view_employee')
def employee_detail(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    documents = employee.documents.all()
    attendance_records = employee.attendance_records.all()[:10]
    leave_requests = employee.leave_requests.all()[:10]

    # Fetch employee costs associated with production batches
    employee_costs = EmployeeCost.objects.filter(employee=employee)

    # Fetch production batches associated with these costs
    production_batches = ProductionBatch.objects.filter(employee_costs_detail__in=employee_costs).distinct() if employee_costs.exists() else []

    context = {
        'employee': employee,
        'documents': documents,
        'attendance_records': attendance_records,
        'leave_requests': leave_requests,
        'employee_costs': employee_costs,
        'production_batches': production_batches,
    }
    return render(request, 'accounts/employee_detail.html', context)
@login_required
@permission_required('accounts.delete_employee')
def employee_terminate(request, pk):
    employee = get_object_or_404(Employee, pk=pk)
    
    if request.method == 'POST':
        employee.employment_status = 'TERMINATED'
        employee.is_active = False
        employee.contract_end_date = timezone.now().date()
        employee.save()
        
        # Removed user deactivation as employees do not have user accounts
        messages.success(request, 'Employee terminated successfully.')
        return redirect('accounts:employee_list')

    return render(request, 'accounts/employee_terminate.html', {
        'employee': employee
    })

@login_required
@permission_required('accounts.add_employeedocument')
def document_upload(request, employee_pk):
    employee = get_object_or_404(Employee, pk=employee_pk)
    
    if request.method == 'POST':
        form = EmployeeDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.employee = employee
            document.save()
            messages.success(request, 'Document uploaded successfully.')
            return redirect('accounts:employee_detail', pk=employee_pk)
    else:
        form = EmployeeDocumentForm()

    return render(request, 'accounts/document_upload.html', {
        'form': form,
        'employee': employee
    })

# Leave list view
@login_required
@permission_required('accounts.view_leave')
def leave_list(request):
    leave_requests = Leave.objects.select_related('employee', 'approved_by').all().order_by('-created_at')

    paginator = Paginator(leave_requests, 10)
    page = request.GET.get('page')
    leave_requests = paginator.get_page(page)

    context = {
        'leave_requests': leave_requests,
    }
    return render(request, 'accounts/leave_list.html', context)

@login_required
def leave_request(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.status = 'PENDING'  # Default status
            
            # Save the leave request
            leave.save()
            messages.success(request, 'Leave request submitted successfully.')
            return redirect('accounts:leave_list')
    else:
        form = LeaveRequestForm()

    return render(request, 'accounts/leave_request.html', {'form': form})



@login_required
@permission_required('accounts.change_leave', raise_exception=True)
def leave_approval(request, pk):
    leave = get_object_or_404(Leave, pk=pk)

    if request.method == 'POST':
        form = LeaveApprovalForm(request.POST, instance=leave)
        if form.is_valid():
            leave = form.save(commit=False)
            
            # Check if the user has a superuser or admin profile
            if hasattr(request.user, 'superuserprofile'):
                leave.approved_by = request.user.superuserprofile.user.employee
            elif hasattr(request.user, 'adminprofile'):
                leave.approved_by = request.user.adminprofile.user.employee
            else:
                messages.error(request, 'You do not have permission to approve this leave.')
                return redirect('accounts:leave_list')

            # Change the leave status to approved
            leave.status = 'APPROVED'
            leave.approved_at = timezone.now()
            leave.save()
            messages.success(request, 'Leave request approved successfully.')
            return redirect('accounts:leave_list')
    else:
        form = LeaveApprovalForm(instance=leave)

    return render(request, 'accounts/leave_approval.html', {
        'form': form,
        'leave': leave
    })

@login_required
@permission_required('accounts.add_attendance')
def attendance_upload(request):
    if request.method == 'POST':
        form = AttendanceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            date = form.cleaned_data['date']
            
            try:
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                
                for row in reader:
                    employee = Employee.objects.get(employee_id=row['employee_id'])
                    Attendance.objects.create(
                        employee=employee,
                        date=date,
                        time_in=datetime.strptime(row['time_in'], '%H:%M').time(),
                        time_out=datetime.strptime(row['time_out'], '%H:%M').time() if row['time_out'] else None,
                        status=row['status'],
                        notes=row.get('notes', '')
                    )
                
                messages.success(request, 'Attendance records uploaded successfully.')
                return redirect('accounts:attendance_list')
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
    else:
        form = AttendanceUploadForm()

    return render(request, 'accounts/attendance_upload.html', {'form': form})

@login_required
def attendance_list(request):
    date_filter = request.GET.get('date')
    department_filter = request.GET.get('department')

    attendance_records = Attendance.objects.all()

    if date_filter:
        attendance_records = attendance_records.filter(date=date_filter)

    if department_filter:
        attendance_records = attendance_records.filter(
            employee__department_id=department_filter
        )

    paginator = Paginator(attendance_records, 50)
    page = request.GET.get('page')
    attendance_records = paginator.get_page(page)

    departments = Department.objects.all()

    context = {
        'attendance_records': attendance_records,
        'departments': departments,
        'date_filter': date_filter,
        'department_filter': department_filter,
    }
    return render(request, 'accounts/attendance_list.html', context)

# Profile view for logged-in users
@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

# Password change view
@login_required
def password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('accounts:profile_view')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/auth/password_change.html', {'form': form})


# DEPARTMENT VIEWS
@login_required
@permission_required('accounts.view_department')
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'accounts/department_list.html', {'departments': departments})

@login_required
@permission_required('accounts.add_department')
def department_create(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department created successfully.')
            return redirect('accounts:department_list')
    else:
        form = DepartmentForm()
    
    return render(request, 'accounts/department_form.html', {'form': form, 'title': 'Create Department'})

@login_required
@permission_required('accounts.change_department')
def department_update(request, pk):
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department updated successfully.')
            return redirect('accounts:department_list')
    else:
        form = DepartmentForm(instance=department)

    return render(request, 'accounts/department_form.html', {'form': form, 'title': 'Update Department'})

@login_required
@permission_required('accounts.delete_department')
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)

    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Department deleted successfully.')
        return redirect('accounts:department_list')

    return render(request, 'accounts/department_confirm_delete.html', {'department': department})