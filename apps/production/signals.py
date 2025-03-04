# apps/production/signals.py
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ProductionBatch, HistoricalData

@receiver(post_save, sender=ProductionBatch)
def create_or_update_historical_data(sender, instance, created, **kwargs):
    # Create a new HistoricalData entry for the batch
    historical_data = HistoricalData(
        batch=instance,  # Set the foreign key to the ProductionBatch instance
        quantity_produced=instance.quantity_produced,
        quantity_rejected=instance.quantity_rejected,
        status=instance.status,
        selling_price=float(instance.schedule.product.selling_price) if hasattr(instance.schedule.product, 'selling_price') else 0.0,
        production_date=instance.start_time.date(),
        quality_check_results=[
            {
                'check_date': qc.check_date.isoformat(),
                'strength_test': float(qc.strength_test) if isinstance(qc.strength_test, Decimal) else qc.strength_test,
                'result': qc.result,
            } for qc in instance.quality_checks.all()
        ]
    )
    
    historical_data.save()