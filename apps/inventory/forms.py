from django import forms
from .models import (
    Supplier, MaterialCategory, RawMaterial, PurchaseOrder, 
    PurchaseOrderItem, StockReceipt, StockReceiptItem, 
    StockAdjustment, StockMovement
)

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = '__all__'
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'address': forms.Textarea(attrs={'rows': 3}),
        }

class MaterialCategoryForm(forms.ModelForm):
    class Meta:
        model = MaterialCategory
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class RawMaterialForm(forms.ModelForm):
    class Meta:
        model = RawMaterial
        fields = '__all__'
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }



class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        exclude = ['created_by', 'approved_by']
        fields = [
            'po_number', 
            'supplier', 
            'order_date', 
            'expected_delivery_date', 
            'notes', 
            'status', 
            'tax_type', 
            'tax_rate', 
            'total_amount', 
            'tax_amount', 
            'shipping_amount', 
            'discount_amount'
        ]  # Include all required fields
        widgets = {
            'order_date': forms.DateInput(attrs={'type': 'date'}),
            'expected_delivery_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'tax_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'total_amount': forms.NumberInput(attrs={'step': '0.01', 'readonly': 'readonly'}),
            'tax_amount': forms.NumberInput(attrs={'step': '0.01', 'readonly': 'readonly'}),
            'shipping_amount': forms.NumberInput(attrs={'step': '0.01'}),
            'discount_amount': forms.NumberInput(attrs={'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        # Add any additional validation here if needed
        return cleaned_data



class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['material', 'quantity', 'unit_price', 'tax_type', 'tax_rate', 'notes']  # Added tax_type
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.01'}),
            'unit_price': forms.NumberInput(attrs={'step': '0.01'}),
            'tax_rate': forms.NumberInput(attrs={'step': '0.01'}),  # Ensure tax_rate accepts decimal input
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

PurchaseOrderItemFormSet = forms.inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    extra=1,
    can_delete=True
)

class StockReceiptForm(forms.ModelForm):
    class Meta:
        model = StockReceipt
        fields = ['receipt_date', 'received_by', 'notes']
        widgets = {
            'receipt_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

class StockReceiptItemForm(forms.ModelForm):
    class Meta:
        model = StockReceiptItem
        fields = ['quantity', 'batch_number', 'manufacturing_date', 
                  'expiry_date', 'quality_check_status', 'notes']
        widgets = {
            'manufacturing_date': forms.DateInput(attrs={'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

StockReceiptItemFormSet = forms.inlineformset_factory(
    StockReceipt,
    StockReceiptItem,
    form=StockReceiptItemForm,
    extra=1,
    can_delete=True
)

class StockAdjustmentForm(forms.ModelForm):
    class Meta:
        model = StockAdjustment
        exclude = ['adjusted_by', 'approved_by']
        widgets = {
            'adjustment_date': forms.DateInput(attrs={'type': 'date'}),
            'reason': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

class StockMovementForm(forms.ModelForm):
    class Meta:
        model = StockMovement
        exclude = ['created_by']
        widgets = {
            'movement_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}
            ),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }