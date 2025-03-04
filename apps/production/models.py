from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from apps.accounts.models import Employee
from apps.inventory.models import RawMaterial
from apps.products.models import Product
from django.utils import timezone
import uuid

def format_currency(value):
    """Format value as KES currency."""
    return f"KES {value:,.2f}" if value is not None else "KES 0.00"

class ProductionLine(models.Model):
    PRODUCTION_TYPE_CHOICES = [
        ('CONTINUOUS', 'Continuous Production'),
        ('BATCH', 'Batch Production'),
        ('CUSTOM', 'Custom Production')
    ]

    STATUS_CHOICES = [
        ('OPERATIONAL', 'Operational'),
        ('MAINTENANCE', 'Under Maintenance'),
        ('BREAKDOWN', 'Breakdown'),
        ('INACTIVE', 'Inactive')
    ]

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    production_type = models.CharField(
        max_length=20,
        choices=PRODUCTION_TYPE_CHOICES,
        default='BATCH'
    )
    description = models.TextField()
    location = models.CharField(max_length=100)
    capacity_per_hour = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    optimal_crew_size = models.PositiveIntegerField()
    installation_date = models.DateField()
    last_maintenance_date = models.DateField()
    next_maintenance_date = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OPERATIONAL'
    )
    supervisor = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name='supervised_lines'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        permissions = [
            ("can_schedule_maintenance", "Can schedule maintenance"),
            ("can_modify_capacity", "Can modify production line capacity"),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    def clean(self):
        if self.next_maintenance_date <= timezone.now().date():
            raise ValidationError('Next maintenance date must be in the future')
        if self.next_maintenance_date <= self.last_maintenance_date:
            raise ValidationError('Next maintenance date must be after last maintenance date')

class ProductionSchedule(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Urgent')
    ]

    STATUS_CHOICES = [
        ('SCHEDULED', 'Scheduled'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('DELAYED', 'Delayed')
    ]

    production_line = models.ForeignKey(
        ProductionLine,
        on_delete=models.CASCADE,
        related_name='schedules'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='production_schedules'
    )
    quantity_planned = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=2
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='SCHEDULED'
    )
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_schedules'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time', '-priority']
        permissions = [
            ("can_modify_schedule", "Can modify production schedule"),
            ("can_cancel_schedule", "Can cancel production schedule"),
        ]

    def __str__(self):
        return f"{self.production_line.code} - {self.product.name} ({self.start_time})"

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError('End time must be after start time')
        if self.start_time < timezone.now():
            raise ValidationError('Start time cannot be in the past')

class ProductionBatch(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('QUALITY_CHECK', 'Quality Check'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected')
    ]

    batch_number = models.CharField(
        max_length=50,
        unique=True,
        default=f"BATCH-{uuid.uuid4().hex[:8].upper()}"
    )
    schedule = models.ForeignKey(
        ProductionSchedule,
        on_delete=models.CASCADE,
        related_name='batches'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    quantity_produced = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    quantity_rejected = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    supervisor = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name='supervised_batches'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ("can_approve_batch", "Can approve production batch"),
            ("can_reject_batch", "Can reject production batch"),
        ]

    def __str__(self):
        return self.batch_number

    def calculate_total_cost(self):
        """Calculate total cost based on employee and material costs."""
        total_employee_cost = sum(emp.cost for emp in self.employee_costs_detail.all())
        total_material_cost = sum(mat.quantity_actual * mat.material.cost_per_unit for mat in self.material_usage.all())
        return total_employee_cost + total_material_cost

class EmployeeCost(models.Model):
    batch = models.ForeignKey(
        ProductionBatch,
        on_delete=models.CASCADE,
        related_name='employee_costs_detail'
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )
    hours_worked = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    
    @property
    def cost(self):
        """Calculate the cost for the employee based on hours worked and rate, formatted as KES."""
        return format_currency(self.hours_worked * self.hourly_rate)

    def __str__(self):
        return f"{self.employee.first_name} {self.employee.last_name} - {self.batch.batch_number}"

    class Meta:
        unique_together = ('batch', 'employee')  # Prevent duplicate entries
        verbose_name = 'Employee Cost'
        verbose_name_plural = 'Employee Costs'

class BatchMaterialUsage(models.Model):
    batch = models.ForeignKey(
        ProductionBatch,
        on_delete=models.CASCADE,
        related_name='material_usage'
    )
    material = models.ForeignKey(
        RawMaterial,
        on_delete=models.CASCADE,
        related_name='batch_usage'
    )
    quantity_planned = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    quantity_actual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    wastage = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0
    )
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['batch', 'material']
        ordering = ['batch', 'material']

    def __str__(self):
        return f"{self.batch.batch_number} - {self.material.name}"

class QualityCheck(models.Model):
    RESULT_CHOICES = [
        ('PASSED', 'Passed'),
        ('FAILED', 'Failed'),
        ('PENDING', 'Pending Review')
    ]

    batch = models.ForeignKey(
        ProductionBatch,
        on_delete=models.CASCADE,
        related_name='quality_checks'
    )
    check_date = models.DateTimeField()
    strength_test = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    moisture_content = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    density = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    result = models.CharField(
        max_length=20,
        choices=RESULT_CHOICES,
        default='PENDING'
    )
    inspector = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name='inspections'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-check_date']
        permissions = [
            ("can_perform_quality_check", "Can perform quality check"),
            ("can_approve_quality_check", "Can approve quality check"),
        ]

    def __str__(self):
        return f"{self.batch.batch_number} - {self.check_date}"

class MaintenanceLog(models.Model):
    MAINTENANCE_TYPE_CHOICES = [
        ('PREVENTIVE', 'Preventive Maintenance'),
        ('CORRECTIVE', 'Corrective Maintenance'),
        ('EMERGENCY', 'Emergency Maintenance')
    ]

    production_line = models.ForeignKey(
        ProductionLine,
        on_delete=models.CASCADE,
        related_name='maintenance_logs'
    )
    maintenance_type = models.CharField(
        max_length=20,
        choices=MAINTENANCE_TYPE_CHOICES
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    performed_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name='maintenance_performed'
    )
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    description = models.TextField()
    parts_replaced = models.TextField(blank=True)
    next_maintenance_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return f"{self.production_line.code} - {self.maintenance_type} ({self.start_time})"
    

class HistoricalData(models.Model):
    batch = models.ForeignKey(
        ProductionBatch, 
        related_name='historical_data', 
        on_delete=models.CASCADE
    )
    quantity_produced = models.PositiveIntegerField()
    quantity_rejected = models.PositiveIntegerField()
    status = models.CharField(max_length=50)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    production_date = models.DateField(default=timezone.now)
    quality_check_results = models.JSONField(default=dict)  # Store results as JSON

    class Meta:
        verbose_name = 'Historical Data'
        verbose_name_plural = 'Historical Data'

    def __str__(self):
        return f"Batch {self.batch.batch_number} - {self.production_date}"