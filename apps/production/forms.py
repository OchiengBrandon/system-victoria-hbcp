from django import forms
from django.core.exceptions import ValidationError
from .models import *

class ProductionLineForm(forms.ModelForm):
    class Meta:
        model = ProductionLine
        exclude = ['created_at', 'updated_at']
        widgets = {
            'installation_date': forms.DateInput(attrs={'type': 'date'}),
            'last_maintenance_date': forms.DateInput(attrs={'type': 'date'}),
            'next_maintenance_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        installation_date = cleaned_data.get('installation_date')
        last_maintenance_date = cleaned_data.get('last_maintenance_date')
        next_maintenance_date = cleaned_data.get('next_maintenance_date')

        if installation_date and last_maintenance_date:
            if last_maintenance_date < installation_date:
                raise ValidationError('Last maintenance date cannot be before installation date')

        return cleaned_data


class ProductionScheduleForm(forms.ModelForm):
    class Meta:
        model = ProductionSchedule
        exclude = ['created_at', 'updated_at', 'created_by']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        production_line = cleaned_data.get('production_line')

        if start_time and end_time and production_line:
            # Check for schedule conflicts
            conflicts = ProductionSchedule.objects.filter(
                production_line=production_line,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exclude(pk=self.instance.pk if self.instance else None)

            if conflicts.exists():
                raise ValidationError('Schedule conflicts with existing production schedule')

            # Ensure end time is after start time
            if end_time <= start_time:
                raise ValidationError('End time must be after start time')

            # Ensure start time is not in the past
            if start_time < timezone.now():
                raise ValidationError('Start time cannot be in the past')

        return cleaned_data


class ProductionBatchForm(forms.ModelForm):
    class Meta:
        model = ProductionBatch
        exclude = ['created_at', 'updated_at', 'batch_number']  # Ensure batch_number is managed correctly
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        quantity_produced = cleaned_data.get('quantity_produced')
        quantity_rejected = cleaned_data.get('quantity_rejected')

        if quantity_produced is not None and quantity_rejected is not None:
            if quantity_rejected > quantity_produced:
                raise ValidationError('Rejected quantity cannot exceed produced quantity')

        return cleaned_data


class BatchMaterialUsageForm(forms.ModelForm):
    class Meta:
        model = BatchMaterialUsage
        fields = ['material', 'quantity_planned', 'quantity_actual', 'wastage', 'notes', 'recorded_by']



class EmployeeCostForm(forms.ModelForm):
    class Meta:
        model = EmployeeCost
        fields = ['employee', 'hours_worked', 'hourly_rate']

    def __init__(self, *args, **kwargs):
        # Retrieve batch from kwargs and store it for later use
        self.batch = kwargs.pop('batch', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        hours_worked = cleaned_data.get('hours_worked')
        hourly_rate = cleaned_data.get('hourly_rate')
        employee = cleaned_data.get('employee')

        # Validate hours worked
        if hours_worked is not None and hours_worked < 0:
            raise ValidationError('Hours worked cannot be negative.')

        # Validate hourly rate
        if hourly_rate is not None and hourly_rate < 0:
            raise ValidationError('Hourly rate cannot be negative.')

        # Check for duplicate employee in the same batch
        if self.batch and employee:
            if EmployeeCost.objects.filter(batch=self.batch, employee=employee).exists():
                raise ValidationError('This employee is already added to this batch.')

        return cleaned_data  # Return cleaned data without tuple


class QualityCheckForm(forms.ModelForm):
    class Meta:
        model = QualityCheck
        exclude = ['created_at', 'updated_at']
        widgets = {
            'check_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        strength_test = cleaned_data.get('strength_test')
        moisture_content = cleaned_data.get('moisture_content')
        density = cleaned_data.get('density')

        # Add specific validation rules for concrete quality parameters
        if strength_test and strength_test < 17:  # Example minimum strength requirement
            raise ValidationError('Strength test result below minimum requirement')

        if moisture_content and (moisture_content < 5 or moisture_content > 40):
            raise ValidationError('Moisture content out of acceptable range (5-40%)')

        return cleaned_data


class MaintenanceLogForm(forms.ModelForm):
    class Meta:
        model = MaintenanceLog
        exclude = ['created_at', 'updated_at']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'next_maintenance_date': forms.DateInput(attrs={'type': 'date'}),
        }



class ProductionReportForm(forms.Form):
    start_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    production_line = forms.ModelChoiceField(
        queryset=ProductionLine.objects.all(),
        required=False,
        empty_label="All"
    )
    report_format = forms.ChoiceField(choices=[
        ('CSV', 'CSV'),
        ('EXCEL', 'Excel'),
        ('PDF', 'PDF')
    ])
    report_type = forms.ChoiceField(choices=[
        ('summary', 'Production Summary Report'),
        ('detailed', 'Detailed Production Report'),
        ('daily', 'Daily Production Report'),
        ('weekly', 'Weekly Production Report'),
        ('monthly', 'Monthly Production Report')
    ])
# Create formsets
BatchMaterialUsageFormSet = forms.modelformset_factory(BatchMaterialUsage, form=BatchMaterialUsageForm, extra=1)
EmployeeCostFormSet = forms.modelformset_factory(EmployeeCost, form=EmployeeCostForm, extra=1)