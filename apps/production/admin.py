from django.contrib import admin
from .models import (
    HistoricalData,
    ProductionLine,
    ProductionSchedule,
    ProductionBatch,
    EmployeeCost,
    BatchMaterialUsage,
    QualityCheck,
    MaintenanceLog
)

@admin.register(ProductionLine)
class ProductionLineAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'production_type', 'status', 'supervisor', 'created_at')
    search_fields = ('name', 'code')
    list_filter = ('status', 'production_type')

@admin.register(ProductionSchedule)
class ProductionScheduleAdmin(admin.ModelAdmin):
    list_display = ('production_line', 'product', 'start_time', 'end_time', 'status', 'priority')
    search_fields = ('product__name', 'production_line__name')
    list_filter = ('status', 'priority')

@admin.register(ProductionBatch)
class ProductionBatchAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'schedule', 'status', 'quantity_produced', 'created_at')
    search_fields = ('batch_number',)
    list_filter = ('status',)

@admin.register(EmployeeCost)
class EmployeeCostAdmin(admin.ModelAdmin):
    list_display = ('batch', 'employee', 'hours_worked', 'hourly_rate')
    search_fields = ('employee__name', 'batch__batch_number')

@admin.register(BatchMaterialUsage)
class BatchMaterialUsageAdmin(admin.ModelAdmin):
    list_display = ('batch', 'material', 'quantity_planned', 'quantity_actual')
    search_fields = ('batch__batch_number', 'material__name')

@admin.register(QualityCheck)
class QualityCheckAdmin(admin.ModelAdmin):
    list_display = ('batch', 'check_date', 'result', 'inspector')
    search_fields = ('batch__batch_number',)
    list_filter = ('result',)

@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ('production_line', 'maintenance_type', 'start_time', 'performed_by', 'cost')
    search_fields = ('production_line__code', 'performed_by__name')
    list_filter = ('maintenance_type',)


class HistoricalDataAdmin(admin.ModelAdmin):
    list_display = ('batch', 'quantity_produced', 'quantity_rejected', 'status', 'selling_price', 'production_date')
    search_fields = ('batch__batch_number', 'status')  # Search by batch number through the foreign key
    list_filter = ('status', 'production_date')
    ordering = ('-production_date',)  # Order by production date descending

admin.site.register(HistoricalData, HistoricalDataAdmin)