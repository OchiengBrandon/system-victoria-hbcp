from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = CustomUserManager()
    # Add a one-to-one relationship with Employee
    employee = models.OneToOneField(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_profile'
    )
class SuperUserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    special_permission = models.BooleanField(default=True)  # Example field specific to superuser
    additional_info = models.TextField(blank=True)  # Add any specific fields for superuser

    def __str__(self):
        return f"Superuser Profile for {self.user.email}"

class AdminProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    department = models.CharField(max_length=100, blank=True)  # Example field specific to admin
    role_description = models.TextField(blank=True)  # Add any specific fields for admin

    def __str__(self):
        return f"Admin Profile for {self.user.email}"

class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField()
    manager = models.ForeignKey(
        'Employee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_department'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'

    def __str__(self):
        return f"{self.code} - {self.name}"


# Define the Employee model
class Employee(models.Model):
    ROLE_CHOICES = [
        ('WORKER', 'Worker'),
        ('SUPERVISOR', 'Supervisor'),
        ('MANAGER', 'Manager'),
    ]

    EMPLOYMENT_STATUS = [
        ('ACTIVE', 'Active'),
        ('ON_LEAVE', 'On Leave'),
        ('SUSPENDED', 'Suspended'),
        ('TERMINATED', 'Terminated')
    ]

    employee_id = models.CharField(
        max_length=20,
        unique=True,
        validators=[
            RegexValidator(
                regex='^EMP\d{6}$',
                message='Employee ID must be in format EMP followed by 6 digits'
            )
        ]
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        related_name='employees'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS,
        default='ACTIVE'
    )
    
    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    national_id = models.CharField(max_length=20, unique=True)
    phone_primary = models.CharField(max_length=15)
    phone_emergency = models.CharField(max_length=15)
    address_street = models.CharField(max_length=255)
    address_city = models.CharField(max_length=100)
    address_state = models.CharField(max_length=100)
    address_postal = models.CharField(max_length=10)
    
    # Employment Information
    date_joined = models.DateField()
    contract_end_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2)
    bank_account = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=100)
    
    # Skills and Qualifications
    education = models.TextField()
    certifications = models.TextField(blank=True)
    skills = models.TextField(blank=True)
    
    # System Fields
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Self-referential field for manager
    manager = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subordinates'  # To access employees managed by a manager
    )

    class Meta:
        ordering = ['-date_joined']
        verbose_name = 'Employee'
        verbose_name_plural = 'Employees'
        permissions = [
            ("can_view_salary", "Can view salary information"),
            ("can_modify_role", "Can modify employee role"),
            ("can_terminate_employee", "Can terminate employee"),
        ]

    def __str__(self):
        # Updated to include full name for better clarity
        return f"{self.first_name} {self.last_name} - {self.employee_id}"

    def get_full_address(self):
        return f"{self.address_street}, {self.address_city}, {self.address_state} {self.address_postal}"

class EmployeeDocument(models.Model):
    DOCUMENT_TYPES = [
        ('CONTRACT', 'Employment Contract'),
        ('ID', 'Identity Document'),
        ('CERTIFICATE', 'Certificate'),
        ('EVALUATION', 'Performance Evaluation'),
        ('OTHER', 'Other')
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='documents'
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='employee_documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.title}"

class Attendance(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    date = models.DateField()
    time_in = models.TimeField()
    time_out = models.TimeField(null=True, blank=True)
    overtime_hours = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('PRESENT', 'Present'),
            ('ABSENT', 'Absent'),
            ('LATE', 'Late'),
            ('HALF_DAY', 'Half Day')
        ]
    )
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['employee', 'date']
        ordering = ['-date', 'time_in']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.date}"

class Leave(models.Model):
    LEAVE_TYPES = [
        ('ANNUAL', 'Annual Leave'),
        ('SICK', 'Sick Leave'),
        ('EMERGENCY', 'Emergency Leave'),
        ('UNPAID', 'Unpaid Leave')
    ]

    LEAVE_STATUS = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled')
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leave_requests'
    )
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=LEAVE_STATUS,
        default='PENDING'
    )
    approved_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.employee_id} - {self.leave_type} ({self.start_date} to {self.end_date})"