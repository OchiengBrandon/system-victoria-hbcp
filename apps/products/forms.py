from django import forms
from .models import (
    ProductCategory, Product, ProductFormula, FormulaItem, ProductMovement
)

class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['name', 'description', 'parent']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = '__all__'
        exclude = ['current_stock']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'minimum_stock': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'maximum_stock': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'reorder_point': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'standard_cost': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'selling_price': forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
class ProductFormulaForm(forms.ModelForm):
    class Meta:
        model = ProductFormula
        fields = ['product', 'version', 'is_active', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'product': forms.Select(attrs={'class': 'form-select'}),
            'version': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class FormulaItemForm(forms.ModelForm):
    class Meta:
        model = FormulaItem
        fields = ['material', 'quantity', 'notes']
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.001', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'material': forms.Select(attrs={'class': 'form-select'}),
        }

FormulaItemFormSet = forms.inlineformset_factory(
    ProductFormula,
    FormulaItem,
    form=FormulaItemForm,
    extra=1,
    can_delete=True
)

class ProductMovementForm(forms.ModelForm):
    class Meta:
        model = ProductMovement
        fields = [
            'product', 'movement_type', 'quantity', 'reference_number',
            'movement_date', 'notes'
        ]
        widgets = {
            'movement_date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'product': forms.Select(attrs={'class': 'form-select'}),
            'movement_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
        }