from django.contrib import admin
from .models import (
    Supplier, MaterialCategory, RawMaterial,
    PurchaseOrder, PurchaseOrderItem, StockReceipt,
    StockReceiptItem, StockAdjustment, StockMovement
)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'code', 'contact_person')
    list_filter = ('is_active',)

@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    search_fields = ('name',)
    list_filter = ('parent',)

@admin.register(RawMaterial)
class RawMaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'category', 'current_stock', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('category', 'is_active')

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'supplier', 'status', 'order_date', 'created_at')
    search_fields = ('po_number', 'supplier__name')
    list_filter = ('status', 'supplier')

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'material', 'quantity', 'unit_price')
    search_fields = ('purchase_order__po_number', 'material__name')
    list_filter = ('purchase_order', 'material')

@admin.register(StockReceipt)
class StockReceiptAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'purchase_order', 'receipt_date', 'created_at')
    search_fields = ('receipt_number', 'purchase_order__po_number')
    list_filter = ('receipt_date',)

@admin.register(StockReceiptItem)
class StockReceiptItemAdmin(admin.ModelAdmin):
    list_display = ('stock_receipt', 'purchase_order_item', 'quantity', 'batch_number')
    search_fields = ('stock_receipt__receipt_number', 'purchase_order_item__material__name')
    list_filter = ('stock_receipt',)

@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('adjustment_number', 'material', 'adjustment_type', 'quantity', 'adjustment_date')
    search_fields = ('adjustment_number', 'material__name')
    list_filter = ('adjustment_type', 'material')

@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('material', 'movement_type', 'quantity', 'movement_date', 'created_at')
    search_fields = ('material__name', 'movement_type')
    list_filter = ('movement_type',)