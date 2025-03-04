# apps/production/views.py

from django.db import IntegrityError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from datetime import timedelta
import csv
import xlsxwriter
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from .models import *
from .forms import *

# DASHBOARD VIEW
@login_required
def production_dashboard_view(request):
    latest_schedule = ProductionSchedule.objects.order_by('-start_time').first()
    latest_batch = ProductionBatch.objects.order_by('-start_time').first()
    production_lines = ProductionLine.objects.all()

    # Prepare data for the chart
    production_labels = [line.name for line in production_lines]
    production_data = [
        ProductionBatch.objects.filter(schedule__production_line=line)
        .aggregate(total_produced=Sum('quantity_produced'))['total_produced'] or 0
        for line in production_lines
    ]

    return render(request, 'production/dashboard.html', {
        'title': 'Production Dashboard',
        'latest_schedule': latest_schedule,
        'latest_batch': latest_batch,
        'production_labels': production_labels,
        'production_data': production_data,
    })


# SCHEDULE LIST VIEW
@login_required
@permission_required('production.view_productionschedule')
def schedule_list(request):
    search_query = request.GET.get('search', '')
    production_line_filter = request.GET.get('production_line', '')
    schedules = ProductionSchedule.objects.all()

    if search_query:
        schedules = schedules.filter(Q(product__name__icontains=search_query) | Q(quantity_planned__icontains=search_query))

    if production_line_filter:
        schedules = schedules.filter(production_line_id=production_line_filter)

    paginator = Paginator(schedules, 10)
    page = request.GET.get('page')
    schedules = paginator.get_page(page)

    context = {
        'schedules': schedules,
        'search_query': search_query,
        'production_line_filter': production_line_filter,
        'production_lines': ProductionLine.objects.all(),  # Pass all production lines for filtering
    }

    return render(request, 'production/schedule_list.html', context)

# PRODUCTION LINE VIEWS
@login_required
@permission_required('production.view_productionline')
def production_line_list(request):
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    production_lines = ProductionLine.objects.all()

    if search_query:
        production_lines = production_lines.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query)
        )

    if status_filter:
        production_lines = production_lines.filter(status=status_filter)

    # Add statistics for each line
    for line in production_lines:
        line.current_month_production = ProductionBatch.objects.filter(
            schedule__production_line=line,
            start_time__month=timezone.now().month
        ).aggregate(
            total_production=Sum('quantity_produced')
        )['total_production'] or 0

        line.maintenance_due = line.next_maintenance_date <= timezone.now().date()

    paginator = Paginator(production_lines, 10)
    page = request.GET.get('page')
    production_lines = paginator.get_page(page)

    context = {
        'production_lines': production_lines,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': ProductionLine.STATUS_CHOICES
    }
    return render(request, 'production/production_line_list.html', context)

@login_required
@permission_required('production.add_productionline')
def production_line_create(request):
    if request.method == 'POST':
        form = ProductionLineForm(request.POST)
        if form.is_valid():
            production_line = form.save()
            messages.success(request, 'Production line created successfully.')
            return redirect('production:production_line_detail', pk=production_line.pk)
    else:
        form = ProductionLineForm()
    
    return render(request, 'production/production_line_form.html', {
        'form': form,
        'title': 'Create Production Line'
    })

@login_required
@permission_required('production.change_productionline')
def production_line_update(request, pk):
    production_line = get_object_or_404(ProductionLine, pk=pk)
    
    if request.method == 'POST':
        form = ProductionLineForm(request.POST, instance=production_line)
        if form.is_valid():
            form.save()
            messages.success(request, 'Production line updated successfully.')
            return redirect('production:production_line_detail', pk=pk)
    else:
        form = ProductionLineForm(instance=production_line)
    
    return render(request, 'production/production_line_form.html', {
        'form': form,
        'production_line': production_line,
        'title': 'Update Production Line'
    })

@login_required
def production_line_detail(request, pk):
    production_line = get_object_or_404(ProductionLine, pk=pk)
    
    # Get current production schedule
    current_schedule = ProductionSchedule.objects.filter(
        production_line=production_line,
        start_time__lte=timezone.now(),
        end_time__gte=timezone.now()
    ).first()
    
    # Get upcoming schedules
    upcoming_schedules = ProductionSchedule.objects.filter(
        production_line=production_line,
        start_time__gt=timezone.now()
    ).order_by('start_time')[:5]
    
    # Get recent maintenance logs
    recent_maintenance = MaintenanceLog.objects.filter(
        production_line=production_line
    ).order_by('-start_time')[:5]
    
    # Calculate efficiency metrics
    thirty_days_ago = timezone.now() - timedelta(days=30)
    monthly_batches = ProductionBatch.objects.filter(
        schedule__production_line=production_line,
        start_time__gte=thirty_days_ago
    )
    
    total_production = monthly_batches.aggregate(
        total=Sum('quantity_produced')
    )['total'] or 0
    
    rejection_rate = monthly_batches.aggregate(
        rejected=Sum('quantity_rejected')
    )['rejected'] or 0
    
    if total_production > 0:
        rejection_rate = (rejection_rate / total_production) * 100
    else:
        rejection_rate = 0
    
    context = {
        'production_line': production_line,
        'current_schedule': current_schedule,
        'upcoming_schedules': upcoming_schedules,
        'recent_maintenance': recent_maintenance,
        'total_production': total_production,
        'rejection_rate': rejection_rate,
        'can_schedule': request.user.has_perm('production.add_productionschedule')
    }
    return render(request, 'production/production_line_detail.html', context)

# PRODUCTION SCHEDULE VIEWS
@login_required
@permission_required('production.add_productionschedule')
def schedule_create(request, line_pk=None):
    if request.method == 'POST':
        form = ProductionScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.created_by = request.user.employee
            schedule.save()
            messages.success(request, 'Production schedule created successfully.')
            return redirect('production:schedule_detail', pk=schedule.pk)
    else:
        initial = {'production_line': line_pk} if line_pk else {}
        form = ProductionScheduleForm(initial=initial)
    
    return render(request, 'production/schedule_form.html', {
        'form': form,
        'title': 'Create Production Schedule'
    })

@login_required
def schedule_detail(request, pk):
    schedule = get_object_or_404(ProductionSchedule, pk=pk)
    batches = ProductionBatch.objects.filter(schedule=schedule)
    
    
    # Calculate schedule progress
    total_produced = batches.aggregate(total=Sum('quantity_produced'))['total'] or 0
    progress = (total_produced / schedule.quantity_planned) * 100 if schedule.quantity_planned > 0 else 0
    
    context = {
        'schedule': schedule,
        'batches': batches,
        'progress': min(progress, 100),
        'can_create_batch': request.user.has_perm('production.add_productionbatch')
    }
    return render(request, 'production/schedule_detail.html', context)

# PRODUCTION BATCH VIEWS

@login_required
@permission_required('production.add_productionbatch')
def batch_create(request, schedule_pk):
    schedule = get_object_or_404(ProductionSchedule, pk=schedule_pk)

    if request.method == 'POST':
        batch_form = ProductionBatchForm(request.POST)
        if batch_form.is_valid():
            batch = batch_form.save(commit=False)
            batch.schedule = schedule
            batch.save()
            messages.success(request, 'Production batch created successfully.')
            return redirect('production:batch_detail', pk=batch.pk)
    else:
        batch_form = ProductionBatchForm(initial={'schedule': schedule})

    return render(request, 'production/batch_form.html', {
        'batch_form': batch_form,
        'schedule': schedule,
        'title': 'Create Production Batch'
    })


# Add materials to batch
@login_required
@permission_required('production.add_batchmaterialusage')
def add_materials_to_batch(request, batch_pk):
    batch = get_object_or_404(ProductionBatch, pk=batch_pk)

    if request.method == 'POST':
        material_formset = BatchMaterialUsageFormSet(request.POST)
        if material_formset.is_valid():
            for form in material_formset:
                material_usage = form.save(commit=False)
                material_usage.batch = batch
                material_usage.save()
            messages.success(request, 'Materials added successfully.')
            return redirect('production:batch_detail', pk=batch.pk)
    else:
        material_formset = BatchMaterialUsageFormSet(queryset=BatchMaterialUsage.objects.none())

    return render(request, 'production/materials_form.html', {
        'material_formset': material_formset,
        'batch': batch,
        'title': 'Add Materials to Batch'
    })

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import BatchMaterialUsage
from .forms import BatchMaterialUsageForm  # Ensure you have this form created

@login_required
@permission_required('production.change_batchmaterialusage')
def material_usage_update(request, batch_pk, usage_pk):
    # Fetch the material usage entry
    usage = get_object_or_404(BatchMaterialUsage, pk=usage_pk)

    # Ensure the usage belongs to the specified batch
    if usage.batch.pk != batch_pk:
        messages.error(request, 'The specified material usage does not belong to this batch.')
        return redirect('production:batch_detail', pk=batch_pk)

    batch = usage.batch  # Get the associated batch
    
    # Initialize the form with the instance for GET request
    if request.method == 'POST':
        form = BatchMaterialUsageForm(request.POST, instance=usage)  # Populate with POST data
        if form.is_valid():
            form.save()
            messages.success(request, 'Material usage updated successfully.')
            return redirect('production:batch_detail', pk=batch.pk)  # Redirect to the batch detail page
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BatchMaterialUsageForm(instance=usage)  # Populate with existing data for GET request

    return render(request, 'production/materials_form.html', {
        'form': form,
        'usage': usage,
        'batch': batch,  # Ensure the batch is passed to the template
    })
# Delete material usage
@login_required
@permission_required('production.delete_batchmaterialusage')
def material_usage_delete(request, batch_pk, pk):
    material_usage = get_object_or_404(BatchMaterialUsage, pk=pk)
    batch = material_usage.batch  # Get the associated batch

    if request.method == 'POST':
        material_usage.delete()
        messages.success(request, 'Material usage deleted successfully.')
        return redirect('production:batch_detail', pk=batch.pk)  # Use batch.pk for redirection

    return render(request, 'production/material_usage_confirm_delete.html', {
        'material_usage': material_usage,
        'batch': batch,
        'title': 'Delete Material Usage'
    })

# Add employee costs to batch
@login_required
@permission_required('production.add_employeecost')
def add_employee_costs_to_batch(request, batch_pk):
    batch = get_object_or_404(ProductionBatch, pk=batch_pk)

    if request.method == 'POST':
        employee_formset = EmployeeCostFormSet(request.POST)

        if employee_formset.is_valid():
            existing_employees = set()  # Track employee IDs to prevent duplicates
            errors_occurred = False  # Flag to track if any errors occurred

            for form in employee_formset:
                employee_cost = form.save(commit=False)
                employee_cost.batch = batch

                # Check for duplicates
                if employee_cost.employee.id in existing_employees:
                    form.add_error('employee', 'This employee has already been added to the batch.')
                    errors_occurred = True  # Set flag if an error occurs
                    continue  # Skip saving this form

                existing_employees.add(employee_cost.employee.id)

                try:
                    employee_cost.save()
                except IntegrityError:
                    form.add_error('employee', 'This employee is already associated with the batch.')
                    errors_occurred = True  # Set flag if an error occurs

            if not errors_occurred:
                messages.success(request, 'Employee costs added successfully.')
                return redirect('production:batch_detail', pk=batch.pk)

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        employee_formset = EmployeeCostFormSet(queryset=EmployeeCost.objects.none())

    return render(request, 'production/employee_costs_form.html', {
        'employee_formset': employee_formset,
        'batch': batch,
        'title': 'Add Employee Costs to Batch'
    })

# Update employee cost
@login_required
@permission_required('production.change_employeecost')
def employee_cost_update(request, batch_pk, cost_pk):
    # Fetch the employee cost entry
    cost = get_object_or_404(EmployeeCost, pk=cost_pk)

    # Ensure the cost entry belongs to the specified batch
    if cost.batch.pk != batch_pk:
        messages.error(request, 'The specified employee cost does not belong to this batch.')
        return redirect('production:batch_detail', pk=batch_pk)

    batch = cost.batch  # Get the associated batch
    
    # Initialize the form with the instance for GET request
    if request.method == 'POST':
        form = EmployeeCostForm(request.POST, instance=cost)  # Populate with POST data
        if form.is_valid():
            form.save()
            messages.success(request, 'Employee cost updated successfully.')
            return redirect('production:batch_detail', pk=batch.pk)  # Redirect to the batch detail page
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = EmployeeCostForm(instance=cost)  # Populate with existing data for GET request

    return render(request, 'production/employee_costs_form.html', {
        'form': form,
        'cost': cost,
        'batch': batch,  # Ensure the batch is passed to the template
    })

# Delete employee cost
@login_required
@permission_required('production.delete_employeecost')
def employee_cost_delete(request, batch_pk, pk):
    employee_cost = get_object_or_404(EmployeeCost, pk=pk)
    batch = employee_cost.batch  # Get the associated batch

    if request.method == 'POST':
        employee_cost.delete()
        messages.success(request, 'Employee cost deleted successfully.')
        return redirect('production:batch_detail', pk=batch.pk)  # Use batch.pk for redirection

    return render(request, 'production/employee_cost_confirm_delete.html', {
        'employee_cost': employee_cost,
        'batch': batch,
        'title': 'Delete Employee Cost'
    })

@login_required
def batch_detail(request, pk):
    batch = get_object_or_404(ProductionBatch, pk=pk)
    material_usage = BatchMaterialUsage.objects.filter(batch=batch)
    quality_checks = QualityCheck.objects.filter(batch=batch)
    employee_costs = EmployeeCost.objects.filter(batch=batch) 
    
    context = {
        'batch': batch,
        'material_usage': material_usage,
        'employee_costs': employee_costs,
        'quality_checks': quality_checks,
        'can_add_quality_check': request.user.has_perm('production.add_qualitycheck'),
        'can_update_batch': request.user.has_perm('production.change_productionbatch')
    }
    return render(request, 'production/batch_detail.html', context)

@login_required
@permission_required('production.change_productionbatch')
def batch_update(request, pk):
    batch = get_object_or_404(ProductionBatch, pk=pk)
    schedule = batch.schedule 

    if request.method == 'POST':
        batch_form = ProductionBatchForm(request.POST, instance=batch)
        material_formset = BatchMaterialUsageFormSet(request.POST, queryset=BatchMaterialUsage.objects.filter(batch=batch))
        employee_formset = EmployeeCostFormSet(request.POST, queryset=EmployeeCost.objects.filter(batch=batch))

        if batch_form.is_valid() and material_formset.is_valid() and employee_formset.is_valid():
            batch_form.save()

            # Update material usage
            for form in material_formset:
                material_usage = form.save(commit=False)
                material_usage.batch = batch
                material_usage.save()

            # Update employee costs
            for form in employee_formset:
                employee_cost = form.save(commit=False)
                employee_cost.batch = batch
                employee_cost.save()

            messages.success(request, 'Batch updated successfully.')
            return redirect('production:batch_detail', pk=batch.pk)
        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        batch_form = ProductionBatchForm(instance=batch)
        material_formset = BatchMaterialUsageFormSet(queryset=BatchMaterialUsage.objects.filter(batch=batch))
        employee_formset = EmployeeCostFormSet(queryset=EmployeeCost.objects.filter(batch=batch))
        
    return render(request, 'production/batch_form.html', {
        'batch_form': batch_form,
        'material_formset': material_formset,
        'employee_formset': employee_formset,
        'batch': batch,
        'schedule': schedule,
        'title': 'Update Production Batch'
    })

# QUALITY CHECK VIEWS
@login_required
@permission_required('production.add_qualitycheck')
def quality_check_create(request, batch_pk):
    batch = get_object_or_404(ProductionBatch, pk=batch_pk)
    
    if request.method == 'POST':
        form = QualityCheckForm(request.POST)
        if form.is_valid():
            quality_check = form.save(commit=False)
            quality_check.batch = batch
            quality_check.inspector = request.user.employee
            quality_check.save()
            
            # Update batch status based on quality check result
            if quality_check.result == 'FAILED':
                batch.status = 'REJECTED'
            elif quality_check.result == 'PASSED':
                batch.status = 'COMPLETED'
            batch.save()
            
            messages.success(request, 'Quality check recorded successfully.')
            return redirect('production:batch_detail', pk=batch_pk)
    else:
        form = QualityCheckForm()
    
    return render(request, 'production/quality_check_form.html', {
        'form': form,
        'batch': batch
    })

# MAINTENANCE VIEWS
@login_required
@permission_required('production.add_maintenancelog')
def maintenance_create(request, line_pk):
    production_line = get_object_or_404(ProductionLine, pk=line_pk)
    
    if request.method == 'POST':
        form = MaintenanceLogForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.production_line = production_line
            maintenance.performed_by = request.user.employee
            maintenance.save()
            
            # Update production line maintenance dates
            production_line.last_maintenance_date = maintenance.start_time.date()
            production_line.next_maintenance_date = maintenance.next_maintenance_date
            production_line.save()
            
            messages.success(request, 'Maintenance log recorded successfully.')
            return redirect('production:production_line_detail', pk=line_pk)
    else:
        form = MaintenanceLogForm()
    
    return render(request, 'production/maintenance_form.html', {
        'form': form,
        'production_line': production_line
    })

# REPORT GENERATION VIEWS

@login_required
def generate_production_report(request):
    if request.method == 'POST':
        form = ProductionReportForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']
            production_line = form.cleaned_data['production_line']
            report_format = form.cleaned_data['report_format']
            report_type = form.cleaned_data['report_type']

            # Query production data
            batches = ProductionBatch.objects.filter(start_time__date__range=[start_date, end_date])
            if production_line:
                batches = batches.filter(schedule__production_line=production_line)

            # Prepare data based on report type
            report_data = []
            if report_type == 'summary':
                report_data = batches.values('schedule__product__name').annotate(total_quantity=Sum('quantity_produced'))
            elif report_type == 'detailed':
                report_data = batches
            elif report_type in ['daily', 'weekly', 'monthly']:
                if report_type == 'daily':
                    report_data = batches.values('start_time__date').annotate(total_quantity=Sum('quantity_produced'))
                elif report_type == 'weekly':
                    report_data = batches.extra(select={'week': "EXTRACT(WEEK FROM start_time)"}).values('week').annotate(total_quantity=Sum('quantity_produced'))
                elif report_type == 'monthly':
                    report_data = batches.extra(select={'month': "EXTRACT(MONTH FROM start_time)"}).values('month').annotate(total_quantity=Sum('quantity_produced'))

            # Generate CSV report
            if report_format == 'CSV':
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="production_report.csv"'
                writer = csv.writer(response)
                writer.writerow(['Batch Number', 'Product', 'Quantity', 'Status', 'Start Time', 'End Time'])

                for batch in report_data:
                    if report_type == 'detailed':
                        writer.writerow([
                            batch.batch_number,
                            batch.schedule.product.name,
                            batch.quantity_produced,
                            batch.status,
                            batch.start_time,
                            batch.end_time
                        ])
                    else:
                        writer.writerow([
                            batch['schedule__product__name'] if 'schedule__product__name' in batch else batch['start_time__date'],
                            batch['total_quantity']
                        ])
                return response

            # Generate Excel report
            elif report_format == 'EXCEL':
                output = BytesIO()
                workbook = xlsxwriter.Workbook(output)
                worksheet = workbook.add_worksheet()

                worksheet.write_row(0, 0, ['Batch Number', 'Product', 'Quantity', 'Status', 'Start Time', 'End Time'])
                for row_num, batch in enumerate(report_data, start=1):
                    if report_type == 'detailed':
                        worksheet.write_row(row_num, 0, [
                            batch.batch_number,
                            batch.schedule.product.name,
                            batch.quantity_produced,
                            batch.status,
                            batch.start_time,
                            batch.end_time
                        ])
                    else:
                        worksheet.write_row(row_num, 0, [
                            batch['schedule__product__name'] if 'schedule__product__name' in batch else batch['start_time__date'],
                            batch['total_quantity']
                        ])

                workbook.close()
                output.seek(0)

                response = HttpResponse(
                    output.read(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'attachment; filename="production_report.xlsx"'
                return response

            # Generate PDF report
            elif report_format == 'PDF':
                buffer = BytesIO()
                p = canvas.Canvas(buffer, pagesize=letter)
                width, height = letter

                p.drawString(100, height - 100, 'Production Report')
                p.drawString(100, height - 120, f'Date Range: {start_date} to {end_date}')
                y_position = height - 160

                for batch in report_data:
                    if report_type == 'detailed':
                        p.drawString(100, y_position, f'{batch.batch_number} - {batch.schedule.product.name} - {batch.quantity_produced} - {batch.status} - {batch.start_time} - {batch.end_time}')
                    else:
                        p.drawString(100, y_position, f'{batch["schedule__product__name"] if "schedule__product__name" in batch else batch["start_time__date"]} - {batch["total_quantity"]}')
                    y_position -= 20

                p.showPage()
                p.save()
                buffer.seek(0)

                response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="production_report.pdf"'
                return response
    else:
        form = ProductionReportForm()

    return render(request, 'production/report_form.html', {'form': form})

# API ENDPOINTS FOR REAL-TIME MONITORING
@login_required
def production_line_status(request, pk):
    production_line = get_object_or_404(ProductionLine, pk=pk)
    current_batch = ProductionBatch.objects.filter(
        schedule__production_line=production_line,
        status='IN_PROGRESS'
    ).first()
    
    data = {
        'status': production_line.status,
        'current_batch': current_batch.batch_number if current_batch else None,
        'current_product': current_batch.schedule.product.name if current_batch else None,
        'quantity_produced': current_batch.quantity_produced if current_batch else 0,
        'last_updated': timezone.now().isoformat()
    }
    
    return JsonResponse(data)