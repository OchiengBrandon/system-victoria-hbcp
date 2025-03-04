from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Employee, Department, EmployeeDocument, Leave
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email',)

# forms.py

from django import forms
from .models import SuperUserProfile, AdminProfile

class SuperUserProfileForm(forms.ModelForm):
    class Meta:
        model = SuperUserProfile
        fields = ['special_permission', 'additional_info']  # Specify the fields to include in the form

    def __init__(self, *args, **kwargs):
        super(SuperUserProfileForm, self).__init__(*args, **kwargs)
        # Customize the form fields if needed
        self.fields['additional_info'].widget.attrs.update({'placeholder': 'Enter additional information here...'})

class AdminProfileForm(forms.ModelForm):
    class Meta:
        model = AdminProfile
        fields = ['department', 'role_description']  # Specify the fields to include in the form

    def __init__(self, *args, **kwargs):
        super(AdminProfileForm, self).__init__(*args, **kwargs)
        # Customize the form fields if needed
        self.fields['role_description'].widget.attrs.update({'placeholder': 'Describe the admin role here...'})

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        exclude = ['created_at', 'updated_at']  # Removed 'user' and 'last_login'
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'date_joined': forms.DateInput(attrs={'type': 'date'}),
            'contract_end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_employee_id(self):
        employee_id = self.cleaned_data['employee_id']
        if not employee_id.startswith('EMP'):
            raise ValidationError('Employee ID must start with EMP')
        return employee_id

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        exclude = ['created_at', 'updated_at']

    def clean_code(self):
        code = self.cleaned_data['code']
        if not code.isalnum():
            raise ValidationError('Department code must be alphanumeric')
        return code.upper()

class EmployeeDocumentForm(forms.ModelForm):
    class Meta:
        model = EmployeeDocument
        exclude = ['uploaded_at']
        widgets = {
            'expires_at': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_file(self):
        file = self.cleaned_data['file']
        if file.size > 5242880:  # 5MB limit
            raise ValidationError('File size must not exceed 5MB')
        return file


class LeaveRequestForm(forms.ModelForm):
    employee = forms.ModelChoiceField(queryset=Employee.objects.all(), required=True, label="Select Employee")

    leave_type = forms.ChoiceField(choices=Leave.LEAVE_TYPES, required=True)
    reason = forms.CharField(widget=forms.Textarea, required=True)

    class Meta:
        model = Leave
        fields = ['employee', 'leave_type', 'start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        if start_date and end_date:
            if start_date > end_date:
                raise ValidationError('End date must be after start date')

        return cleaned_data

class LeaveApprovalForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = ['status']

class AttendanceUploadForm(forms.Form):
    file = forms.FileField(
        help_text='Upload CSV file with attendance records'
    )
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

