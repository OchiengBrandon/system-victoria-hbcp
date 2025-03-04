from django.contrib import admin
from .models import ProductCategory, Product, ProductFormula, FormulaItem, ProductMovement

# Register your models here.
@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'parent', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('parent',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'current_stock', 'status', 'created_at')
    search_fields = ('name', 'code', 'description')
    list_filter = ('category', 'status')

@admin.register(ProductFormula)
class ProductFormulaAdmin(admin.ModelAdmin):
    list_display = ('product', 'version', 'is_active', 'created_at')
    search_fields = ('product__name', 'version')
    list_filter = ('is_active',)

@admin.register(FormulaItem)
class FormulaItemAdmin(admin.ModelAdmin):
    list_display = ('formula', 'material', 'quantity')
    search_fields = ('formula__product__name', 'material__name')
    list_filter = ('formula',)

@admin.register(ProductMovement)
class ProductMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'movement_type', 'quantity', 'movement_date', 'created_at')
    search_fields = ('product__name', 'reference_number')
    list_filter = ('movement_type',)