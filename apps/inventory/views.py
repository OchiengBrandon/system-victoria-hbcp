# apps/inventory/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from .models import (
    Supplier, MaterialCategory, RawMaterial, PurchaseOrder,
    PurchaseOrderItem, StockReceipt, StockAdjustment, StockMovement
)
from .forms import (
    SupplierForm, MaterialCategoryForm, RawMaterialForm,
    PurchaseOrderForm, PurchaseOrderItemFormSet,
    StockReceiptForm, StockReceiptItemFormSet,
    StockAdjustmentForm, StockMovementForm
)

# Inventory Dashboard View
@login_required
@permission_required('inventory.view_dashboard')
def inventory_dashboard(request):
    total_suppliers = Supplier.objects.count()
    total_materials = RawMaterial.objects.count()
    total_purchase_orders = PurchaseOrder.objects.count()
    total_stock_movements = StockMovement.objects.count()
    
    context = {
        'total_suppliers': total_suppliers,
        'total_materials': total_materials,
        'total_purchase_orders': total_purchase_orders,
        'total_stock_movements': total_stock_movements,
    }
    
    return render(request, 'inventory/dashboard.html', context)

# Supplier Views
@login_required
@permission_required('inventory.view_supplier')
def supplier_list(request):
    query = request.GET.get('q', '')
    status = request.GET.get('status')
    
    suppliers = Supplier.objects.all()
    
    if query:
        suppliers = suppliers.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(contact_person__icontains=query) |
            Q(email__icontains=query)
        )
    
    if status:
        suppliers = suppliers.filter(is_active=status == 'active')
    
    paginator = Paginator(suppliers, 25)
    page = request.GET.get('page')
    suppliers = paginator.get_page(page)
    
    context = {
        'suppliers': suppliers,
        'query': query,
        'status': status
    }
    return render(request, 'inventory/supplier_list.html', context)

@login_required
@permission_required('inventory.add_supplier')
def supplier_create(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Supplier {supplier.name} created successfully.')
            return redirect('inventory:supplier_list')
    else:
        form = SupplierForm()
    
    return render(request, 'inventory/supplier_form.html', {'form': form})

@login_required
@permission_required('inventory.change_supplier')
def supplier_update(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=supplier)
        if form.is_valid():
            supplier = form.save()
            messages.success(request, f'Supplier {supplier.name} updated successfully.')
            return redirect('inventory:supplier_list')
    else:
        form = SupplierForm(instance=supplier)
    
    return render(request, 'inventory/supplier_form.html', {
        'form': form,
        'supplier': supplier
    })

@login_required
@permission_required('inventory.view_supplier')
def supplier_detail(request, pk):
    supplier = get_object_or_404(Supplier, pk=pk)
    purchase_orders = supplier.purchase_orders.all().order_by('-created_at')[:10]
    
    context = {
        'supplier': supplier,
        'purchase_orders': purchase_orders
    }
    return render(request, 'inventory/supplier_detail.html', context)

# Material Category Views
@login_required
@permission_required('inventory.view_materialcategory')
def category_list(request):
    query = request.GET.get('q', '')
    categories = MaterialCategory.objects.all()
    
    if query:
        categories = categories.filter(name__icontains=query)
    
    paginator = Paginator(categories, 25)
    page = request.GET.get('page')
    categories = paginator.get_page(page)
    
    return render(request, 'inventory/category_list.html', {
        'categories': categories,
        'query': query
    })

@login_required
@permission_required('inventory.add_materialcategory')
def category_create(request):
    if request.method == 'POST':
        form = MaterialCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category {category.name} created successfully.')
            return redirect('inventory:category_list')
    else:
        form = MaterialCategoryForm()
    
    return render(request, 'inventory/category_form.html', {'form': form})

@login_required
@permission_required('inventory.change_materialcategory')
def category_update(request, pk):
    category = get_object_or_404(MaterialCategory, pk=pk)
    
    if request.method == 'POST':
        form = MaterialCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category {category.name} updated successfully.')
            return redirect('inventory:category_list')
    else:
        form = MaterialCategoryForm(instance=category)
    
    return render(request, 'inventory/category_form.html', {
        'form': form,
        'category': category
    })

# Raw Material Views
@login_required
@permission_required('inventory.view_rawmaterial')
def material_list(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category')
    status = request.GET.get('status')
    
    materials = RawMaterial.objects.all()
    
    if query:
        materials = materials.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query)
        )
    
    if category:
        materials = materials.filter(category_id=category)
    
    if status:
        materials = materials.filter(is_active=status == 'active')
    
    paginator = Paginator(materials, 25)
    page = request.GET.get('page')
    materials = paginator.get_page(page)
    
    categories = MaterialCategory.objects.all()
    
    context = {
        'materials': materials,
        'categories': categories,
        'query': query,
        'selected_category': category,
        'status': status
    }
    return render(request, 'inventory/material_list.html', context)

@login_required
@permission_required('inventory.add_rawmaterial')
def material_create(request):
    if request.method == 'POST':
        form = RawMaterialForm(request.POST)
        if form.is_valid():
            material = form.save()
            messages.success(request, f'Material {material.name} created successfully.')
            return redirect('inventory:material_list')
    else:
        form = RawMaterialForm()
    
    return render(request, 'inventory/material_form.html', {'form': form})

@login_required
@permission_required('inventory.change_rawmaterial')
def material_update(request, pk):
    material = get_object_or_404(RawMaterial, pk=pk)
    
    if request.method == 'POST':
        form = RawMaterialForm(request.POST, instance=material)
        if form.is_valid():
            material = form.save()
            messages.success(request, f'Material {material.name} updated successfully.')
            return redirect('inventory:material_list')
    else:
        form = RawMaterialForm(instance=material)
    
    return render(request, 'inventory/material_form.html', {
        'form': form,
        'material': material
    })

@login_required
@permission_required('inventory.view_rawmaterial')
def material_detail(request, pk):
    material = get_object_or_404(RawMaterial, pk=pk)
    stock_movements = material.stock_movements.all().order_by('-movement_date')[:10]
    
    context = {
        'material': material,
        'stock_movements': stock_movements
    }
    return render(request, 'inventory/material_detail.html', context)

# Purchase Order Views
@login_required
@permission_required('inventory.view_purchaseorder')
def purchase_order_list(request):
    query = request.GET.get('q', '')
    status = request.GET.get('status')
    supplier = request.GET.get('supplier')
    
    purchase_orders = PurchaseOrder.objects.all()
    
    if query:
        purchase_orders = purchase_orders.filter(
            Q(po_number__icontains=query) |
            Q(supplier__name__icontains=query)
        )
    
    if status:
        purchase_orders = purchase_orders.filter(status=status)
    
    if supplier:
        purchase_orders = purchase_orders.filter(supplier_id=supplier)
    
    paginator = Paginator(purchase_orders, 25)
    page = request.GET.get('page')
    purchase_orders = paginator.get_page(page)
    
    suppliers = Supplier.objects.filter(is_active=True)
    
    context = {
        'purchase_orders': purchase_orders,
        'suppliers': suppliers,
        'query': query,
        'status': status,
        'selected_supplier': supplier
    }
    return render(request, 'inventory/purchase_order_list.html', context)

@login_required
@permission_required('inventory.add_purchaseorder')
def purchase_order_create(request):
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST)
        formset = PurchaseOrderItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            purchase_order = form.save(commit=False)
            purchase_order.created_by = request.user  # Set created_by to the current user
            purchase_order.save()

            items = formset.save(commit=False)
            for item in items:
                item.purchase_order = purchase_order
                item.save()

            purchase_order.calculate_total()  # Calculate total after saving items

            messages.success(request, f'Purchase Order {purchase_order.po_number} created successfully.')
            return redirect('inventory:purchase_order_detail', pk=purchase_order.pk)
        else:
            print("Form or Formset errors:", form.errors, formset.errors)
    else:
        form = PurchaseOrderForm()
        formset = PurchaseOrderItemFormSet()

    return render(request, 'inventory/purchase_order_form.html', {
        'form': form,
        'formset': formset
    })

@login_required
@permission_required('inventory.change_purchaseorder')
def purchase_order_update(request, pk):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)

    # Check if the purchase order is in a modifiable state
    if purchase_order.status not in ['DRAFT', 'PENDING']:
        messages.error(request, 'Cannot modify purchase order in current status.')
        return redirect('inventory:purchase_order_detail', pk=pk)

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=purchase_order)
        formset = PurchaseOrderItemFormSet(request.POST, instance=purchase_order)

        if form.is_valid() and formset.is_valid():
            purchase_order = form.save(commit=False)  # Save the main purchase order
            
            # Set approved_by to the current user if they are allowed to approve
            if request.user.is_staff or request.user.is_superuser:
                purchase_order.approved_by = request.user

            purchase_order.save()  # Save the purchase order

            # Save new items or update existing ones
            items = formset.save(commit=False)
            for item in items:
                if item.id:  # Update existing item
                    existing_item = get_object_or_404(PurchaseOrderItem, pk=item.id)
                    existing_item.quantity = item.quantity
                    existing_item.unit_price = item.unit_price
                    existing_item.tax_rate = item.tax_rate
                    existing_item.tax_type = item.tax_type
                    existing_item.notes = item.notes
                    existing_item.save()  # Save updated item
                else:  # Create new item
                    if PurchaseOrderItem.objects.filter(
                        purchase_order=purchase_order, material=item.material
                    ).exists():
                        formset.add_error(None, "This item already exists in the purchase order.")
                    else:
                        item.purchase_order = purchase_order
                        item.save()  # Save new item

            purchase_order.calculate_total()  # Recalculate total after updates
            messages.success(request, f'Purchase Order {purchase_order.po_number} updated successfully.')
            return redirect('inventory:purchase_order_detail', pk=purchase_order.pk)

        else:
            # Log the specific errors
            print("Form errors:", form.errors)  # Print form errors for debugging
            print("Formset errors:", formset.errors)  # Print formset errors for debugging
            messages.error(request, 'There were errors in your submission.')

    else:
        form = PurchaseOrderForm(instance=purchase_order)
        formset = PurchaseOrderItemFormSet(instance=purchase_order)  # Ensure to pass the instance correctly

    return render(request, 'inventory/purchase_order_form.html', {
        'form': form,
        'formset': formset,
        'purchase_order': purchase_order
    })

@login_required
@permission_required('inventory.view_purchaseorder')
def purchase_order_detail(request, pk):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
    receipts = purchase_order.receipts.all().order_by('-receipt_date')
    
    context = {
        'purchase_order': purchase_order,
        'receipts': receipts
    }
    return render(request, 'inventory/purchase_order_detail.html', context)

@login_required
@permission_required('inventory.delete_purchaseorder')
def purchase_order_delete(request, pk):
    purchase_order = get_object_or_404(PurchaseOrder, pk=pk)
    
    if purchase_order.status not in ['DRAFT']:
        messages.error(request, 'Cannot delete purchase order in current status.')
        return redirect('inventory:purchase_order_detail', pk=pk)
    
    if request.method == 'POST':
        purchase_order.delete()
        messages.success(request, 'Purchase Order deleted successfully.')
        return redirect('inventory:purchase_order_list')
    
    return render(request, 'inventory/purchase_order_confirm_delete.html', {
        'purchase_order': purchase_order
    })

# Stock Receipt Views
@login_required
@permission_required('inventory.view_stockreceipt')
def stock_receipt_list(request):
    query = request.GET.get('q', '')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    receipts = StockReceipt.objects.all()
    
    if query:
        receipts = receipts.filter(
            Q(receipt_number__icontains=query) |
            Q(purchase_order__po_number__icontains=query)
        )
    
    if date_from:
        receipts = receipts.filter(receipt_date__gte=date_from)
    
    if date_to:
        receipts = receipts.filter(receipt_date__lte=date_to)
    
    paginator = Paginator(receipts, 25)
    page = request.GET.get('page')
    receipts = paginator.get_page(page)
    
    context = {
        'receipts': receipts,
        'query': query,
        'date_from': date_from,
        'date_to': date_to
    }
    return render(request, 'inventory/stock_receipt_list.html', context)

@login_required
@permission_required('inventory.add_stockreceipt')
def stock_receipt_create(request, po_id):
    purchase_order = get_object_or_404(PurchaseOrder, pk=po_id)
    
    if purchase_order.status not in ['ORDERED', 'PARTIALLY_RECEIVED']:
        messages.error(request, 'Cannot create receipt for purchase order in current status.')
        return redirect('inventory:purchase_order_detail', pk=po_id)
    
    if request.method == 'POST':
        form = StockReceiptForm(request.POST)
        if form.is_valid():
            receipt = form.save(commit=False)
            receipt.purchase_order = purchase_order
            receipt.save()
            
            formset = StockReceiptItemFormSet(request.POST, instance=receipt)
            if formset.is_valid():
                formset.save()
                messages.success(request, f'Stock Receipt {receipt.receipt_number} created successfully.')
                return redirect('inventory:stock_receipt_detail', pk=receipt.pk)
    else:
        form = StockReceiptForm(initial={'receipt_date': timezone.now().date()})
        formset = StockReceiptItemFormSet()
    
    return render(request, 'inventory/stock_receipt_form.html', {
        'form': form,
        'formset': formset,
        'purchase_order': purchase_order
    })

@login_required
@permission_required('inventory.view_stockreceipt')
def stock_receipt_detail(request, pk):
    receipt = get_object_or_404(StockReceipt, pk=pk)
    return render(request, 'inventory/stock_receipt_detail.html', {
        'receipt': receipt
    })

# Stock Adjustment Views
@login_required
@permission_required('inventory.view_stockadjustment')
def stock_adjustment_list(request):
    query = request.GET.get('q', '')
    adjustment_type = request.GET.get('type')
    
    adjustments = StockAdjustment.objects.all()
    
    if query:
        adjustments = adjustments.filter(
            Q(adjustment_number__icontains=query) |
            Q(material__name__icontains=query)
        )
    
    if adjustment_type:
        adjustments = adjustments.filter(adjustment_type=adjustment_type)
    
    paginator = Paginator(adjustments, 25)
    page = request.GET.get('page')
    adjustments = paginator.get_page(page)
    
    context = {
        'adjustments': adjustments,
        'query': query,
        'adjustment_type': adjustment_type
    }
    return render(request, 'inventory/stock_adjustment_list.html', context)

@login_required
@permission_required('inventory.add_stockadjustment')
def stock_adjustment_create(request):
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST)
        if form.is_valid():
            adjustment = form.save(commit=False)
            adjustment.adjusted_by = request.user.employee
            adjustment.save()
            messages.success(request, f'Stock Adjustment {adjustment.adjustment_number} created successfully.')
            return redirect('inventory:stock_adjustment_detail', pk=adjustment.pk)
    else:
        form = StockAdjustmentForm(initial={'adjustment_date': timezone.now().date()})
    
    return render(request, 'inventory/stock_adjustment_form.html', {'form': form})

@login_required
@permission_required('inventory.view_stockadjustment')
def stock_adjustment_detail(request, pk):
    adjustment = get_object_or_404(StockAdjustment, pk=pk)
    return render(request, 'inventory/stock_adjustment_detail.html', {
        'adjustment': adjustment
    })

# Stock Movement Views
@login_required
@permission_required('inventory.view_stockmovement')
def stock_movement_list(request):
    query = request.GET.get('q', '')
    movement_type = request.GET.get('type')
    material_id = request.GET.get('material')
    
    movements = StockMovement.objects.all()
    
    if query:
        movements = movements.filter(
            Q(reference_number__icontains=query) |
            Q(material__name__icontains=query)
        )
    
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    
    if material_id:
        movements = movements.filter(material_id=material_id)
    
    paginator = Paginator(movements, 25)
    page = request.GET.get('page')
    movements = paginator.get_page(page)
    
    materials = RawMaterial.objects.filter(is_active=True)
    
    context = {
        'movements': movements,
        'materials': materials,
        'query': query,
        'movement_type': movement_type,
        'selected_material': material_id
    }
    return render(request, 'inventory/stock_movement_list.html', context)

@login_required
@permission_required('inventory.view_stockmovement')
def stock_movement_detail(request, pk):
    movement = get_object_or_404(StockMovement, pk=pk)
    return render(request, 'inventory/stock_movement_detail.html', {
        'movement': movement
    })

# Stock Movement Update View
@login_required
@permission_required('inventory.change_stockmovement')
def stock_movement_update(request, pk):
    movement = get_object_or_404(StockMovement, pk=pk)

    if request.method == 'POST':
        form = StockMovementForm(request.POST, instance=movement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Stock Movement updated successfully.')
            return redirect('inventory:stock_movement_list')
    else:
        form = StockMovementForm(instance=movement)

    return render(request, 'inventory/stock_movement_form.html', {
        'form': form,
        'movement': movement
    })

# Stock Movement Delete View
@login_required
@permission_required('inventory.delete_stockmovement')
def stock_movement_delete(request, pk):
    movement = get_object_or_404(StockMovement, pk=pk)

    if request.method == 'POST':
        movement.delete()
        messages.success(request, 'Stock Movement deleted successfully.')
        return redirect('inventory:stock_movement_list')

    return render(request, 'inventory/stock_movement_confirm_delete.html', {
        'movement': movement
    })

# Stock Movement Create View
@login_required
@permission_required('inventory.add_stockmovement')
def stock_movement_create(request):
    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Stock Movement created successfully.')
            return redirect('inventory:stock_movement_list')
    else:
        form = StockMovementForm()

    return render(request, 'inventory/stock_movement_form.html', {
        'form': form
    })