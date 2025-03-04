from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.db.models import Q, F, ExpressionWrapper, DecimalField
from django.core.paginator import Paginator
from django.db.models import Sum

from apps.production.models import BatchMaterialUsage, EmployeeCost, ProductionBatch
from .models import (
    ProductCategory, Product, ProductFormula, FormulaItem, ProductMovement, 
)
from .forms import (
    ProductCategoryForm, ProductForm, ProductFormulaForm,
    FormulaItemFormSet, ProductMovementForm
)
# Product Dashboard View
@login_required
@permission_required('products.view_product')
def product_dashboard(request):
    total_products = Product.objects.count()
    total_categories = ProductCategory.objects.count()
    recent_movements = ProductMovement.objects.order_by('-created_at')[:5]  # Adjust the field as necessary

    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'recent_movements': recent_movements,
    }
    return render(request, 'products/dashboard.html', context)

# Product Report View
@login_required
@permission_required('products.view_product')
def product_report(request):
    products = Product.objects.all()
    report_data = []

    for product in products:
        movements = product.stock_movements.all()
        total_movement = sum(movement.quantity for movement in movements)
        report_data.append({
            'product': product,
            'total_movement': total_movement,
            'movements': movements,
        })

    context = {
        'report_data': report_data,
    }
    return render(request, 'products/product_report.html', context)

# Product Category Views
@login_required
@permission_required('products.view_productcategory')
def category_list(request):
    query = request.GET.get('q', '')
    categories = ProductCategory.objects.all()
    
    if query:
        categories = categories.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
    
    paginator = Paginator(categories, 25)
    page = request.GET.get('page')
    categories = paginator.get_page(page)
    
    context = {
        'categories': categories,
        'query': query
    }
    return render(request, 'products/category_list.html', context)

@login_required
@permission_required('products.add_productcategory')
def category_create(request):
    if request.method == 'POST':
        form = ProductCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category {category.name} created successfully.')
            return redirect('products:category_list')
    else:
        form = ProductCategoryForm()
    
    return render(request, 'products/category_form.html', {'form': form})

@login_required
@permission_required('products.change_productcategory')
def category_update(request, pk):
    category = get_object_or_404(ProductCategory, pk=pk)
    
    if request.method == 'POST':
        form = ProductCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category {category.name} updated successfully.')
            return redirect('products:category_list')
    else:
        form = ProductCategoryForm(instance=category)
    
    return render(request, 'products/category_form.html', {
        'form': form,
        'category': category
    })

# Category delete view
@login_required
@permission_required('products.delete_productcategory')
def category_delete(request, pk):
    category = get_object_or_404(ProductCategory, pk=pk)

    if request.method == 'POST':
        category.delete()
        messages.success(request, f'Category {category.name} deleted successfully.')
        return redirect('products:category_list')

    return render(request, 'products/category_delete_confirm.html', {'category': category})

# Product Selling Price Report View

@login_required
@permission_required('production.view_product')
def product_selling_price_report(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Fetch historical batches for the product
    historical_batches = ProductionBatch.objects.filter(schedule__product=product).prefetch_related('quality_checks')

    historical_data = []
    total_employee_cost = Decimal(0)
    total_material_cost = Decimal(0)
    total_quantity_produced = Decimal(0)

    for batch in historical_batches:
        # Calculate total employee cost for the current batch
        employee_cost = EmployeeCost.objects.filter(batch=batch).aggregate(
            total_cost=Sum(ExpressionWrapper(F('hours_worked') * F('hourly_rate'), output_field=DecimalField()))
        )['total_cost'] or Decimal(0)

        # Calculate total material cost for the current batch
        material_cost = BatchMaterialUsage.objects.filter(batch=batch).aggregate(
            total_cost=Sum(ExpressionWrapper(F('quantity_actual') * F('material__cost_per_unit'), output_field=DecimalField()))
        )['total_cost'] or Decimal(0)

        # Calculate total cost for the current batch
        total_cost = employee_cost + material_cost
        
        # Update the total quantity produced
        total_quantity_produced += batch.quantity_produced or Decimal(0)

        # Append historical data for the batch
        historical_data.append({
            'batch_number': batch.batch_number,
            'quantity_produced': batch.quantity_produced,
            'quantity_rejected': batch.quantity_rejected,
            'status': batch.status,
            'quality_check_results': [
                {
                    'check_date': qc.check_date,
                    'strength_test': qc.strength_test,
                    'result': qc.result
                }
                for qc in batch.quality_checks.all()
            ],
            'selling_price': total_cost / (batch.quantity_produced or Decimal(1)),  # Selling price per unit for the batch
            'total_employee_cost': employee_cost,
            'total_material_cost': material_cost,  # Ensure this is included
            'total_cost': total_cost,  # Add total cost for the batch
            'production_date': batch.start_time.date(),
        })

        # Accumulate total costs
        total_employee_cost += employee_cost
        total_material_cost += material_cost

    # Calculate overall total cost
    overall_total_cost = total_employee_cost + total_material_cost

    # Calculate current selling price per single unit for the product
    if total_quantity_produced > 0:
        current_selling_price = (overall_total_cost / total_quantity_produced) * Decimal(1.2)  # Example markup of 20%
    else:
        current_selling_price = Decimal(0)  # Prevent division by zero

    # Prepare detailed calculation information
    calculation_details = {
        'total_employee_cost': total_employee_cost,
        'total_material_cost': total_material_cost,
        'total_cost': overall_total_cost,
        'total_quantity_produced': total_quantity_produced,
        'markup': Decimal(1.2),
        'current_selling_price': current_selling_price,
    }

    context = {
        'product': product,
        'current_selling_price': current_selling_price,
        'historical_data': historical_data,
        'calculation_details': calculation_details,
        'total_batches': historical_batches.count(),  # Total number of batches
        'average_selling_price': current_selling_price / (total_quantity_produced or Decimal(1)),  # Average selling price per unit
    }
    
    return render(request, 'products/product_selling_price_report.html', context)
# Product Views
@login_required
@permission_required('products.view_product')
def product_list(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category')
    status = request.GET.get('status')
    
    products = Product.objects.all()
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(code__icontains=query) |
            Q(description__icontains=query)
        )
    
    if category:
        products = products.filter(category_id=category)
    
    if status:
        products = products.filter(status=status)
    
    paginator = Paginator(products, 25)
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    categories = ProductCategory.objects.all()
    
    context = {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category,
        'status': status
    }
    return render(request, 'products/product_list.html', context)

@login_required
@permission_required('products.add_product')
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product {product.name} created successfully.')
            return redirect('products:product_detail', pk=product.pk)
    else:
        form = ProductForm()
    
    return render(request, 'products/product_form.html', {'form': form})


@login_required
@permission_required('products.change_product')
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product {product.name} updated successfully.')
            return redirect('products:product_detail', pk=product.pk)
        else:
            # Print form errors for debugging
            print("Form errors:", form.errors)  # Debugging line
            
            # Optionally, add an error message for the user
            messages.error(request, 'There were errors in the form. Please correct them and try again.')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'products/product_form.html', {
        'form': form,
        'product': product
    })

@login_required
@permission_required('products.view_product')
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    formulas = product.formulas.all()
    stock_movements = product.stock_movements.all()[:5]
    
    context = {
        'product': product,
        'formulas': formulas,
        'stock_movements': stock_movements
    }
    return render(request, 'products/product_detail.html', context)

# Product Formula Views
@login_required
@permission_required('products.add_productformula')
def formula_create(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    
    if request.method == 'POST':
        form = ProductFormulaForm(request.POST)
        if form.is_valid():
            formula = form.save(commit=False)
            formula.created_by = request.user.employee
            formula.save()
            
            formset = FormulaItemFormSet(request.POST, instance=formula)
            if formset.is_valid():
                formset.save()
                messages.success(request, 'Product formula created successfully.')
                return redirect('products:product_detail', pk=product.pk)
    else:
        form = ProductFormulaForm(initial={'product': product})
        formset = FormulaItemFormSet()
    
    return render(request, 'products/formula/formula_form.html', {
        'form': form,
        'formset': formset,
        'product': product
    })

# Delete Formula
@login_required
@permission_required('products.delete_productformula')
def formula_delete(request, pk):
    formula = get_object_or_404(ProductFormula, pk=pk)

    if request.method == 'POST':
        formula.delete()
        messages.success(request, f'Formula for "{formula.product.name}" - Version "{formula.version}" deleted successfully.')
        return redirect('products:product_detail', pk=formula.product.pk)

    return render(request, 'products/formula/formula_delete_confirm.html', {'formula': formula})

# Formula list
@login_required
@permission_required('products.view_productformula')
def formula_list(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    formulas = product.formulas.all()
    
    context = {
        'product': product,
        'formulas': formulas,
    }
    return render(request, 'products/formula/formula_list.html', context)

# Update Formula
@login_required
@permission_required('products.change_productformula')
def formula_update(request, pk):
    formula = get_object_or_404(ProductFormula, pk=pk)
    product = formula.product  # Fetch the associated product

    if request.method == 'POST':
        form = ProductFormulaForm(request.POST, instance=formula)
        if form.is_valid():
            formula = form.save()
            
            formset = FormulaItemFormSet(request.POST, instance=formula)
            if formset.is_valid():
                formset.save()
                messages.success(request, 'Product formula updated successfully.')
                return redirect('products:product_detail', pk=product.pk)  # Redirect using the product's pk
    else:
        form = ProductFormulaForm(instance=formula)
        formset = FormulaItemFormSet(instance=formula)

    return render(request, 'products/formula/formula_form.html', {
        'form': form,
        'formset': formset,
        'formula': formula,
        'product': product  # Pass the product to the template
    })

# Product Movement Views
@login_required
@permission_required('products.view_productmovement')
def product_movement_list(request):
    query = request.GET.get('q', '')
    movement_type = request.GET.get('type')
    product_id = request.GET.get('product')
    
    movements = ProductMovement.objects.all()
    
    if query:
        movements = movements.filter(
            Q(reference_number__icontains=query) |
            Q(product__name__icontains=query)
        )
    
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    
    if product_id:
        movements = movements.filter(product_id=product_id)
    
    paginator = Paginator(movements, 25)
    page = request.GET.get('page')
    movements = paginator.get_page(page)
    
    products = Product.objects.filter(is_active=True)
    
    context = {
        'movements': movements,
        'products': products,
        'query': query,
        'movement_type': movement_type,
        'selected_product': product_id
    }
    return render(request, 'products/product_movement_list.html', context)

@login_required
@permission_required('products.add_productmovement')
def product_movement_create(request):
    if request.method == 'POST':
        form = ProductMovementForm(request.POST)
        if form.is_valid():
            movement = form.save(commit=False)
            movement.created_by = request.user.employee
            
            movement.save()
            
            # Update product stock
            product = movement.product
            if movement.movement_type in ['PRODUCTION', 'RETURN']:
                product.current_stock = F('current_stock') + movement.quantity
            else:
                product.current_stock = F('current_stock') - movement.quantity
            product.save()
            
            messages.success(request, 'Product movement recorded successfully.')
            return redirect('products:product_movement_list')
    else:
        form = ProductMovementForm()
    
    return render(request, 'products/product_movement_form.html', {'form': form})


# Product Movement Update View
@login_required
@permission_required('products.change_productmovement')
def product_movement_update(request, pk):
    movement = get_object_or_404(ProductMovement, pk=pk)

    if request.method == 'POST':
        form = ProductMovementForm(request.POST, instance=movement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Movement updated successfully.')
            return redirect('products:product_movement_list')
    else:
        form = ProductMovementForm(instance=movement)

    return render(request, 'products/product_movement_form.html', {'form': form, 'movement': movement})

# Product Movement Delete View
@login_required
@permission_required('products.delete_productmovement')
def product_movement_delete(request, pk):
    movement = get_object_or_404(ProductMovement, pk=pk)

    if request.method == 'POST':
        movement.delete()
        messages.success(request, 'Movement deleted successfully.')
        return redirect('products:product_movement_list')

    return render(request, 'products/product_movement_delete_confirm.html', {'movement': movement})