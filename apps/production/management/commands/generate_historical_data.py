from django.core.management.base import BaseCommand
from apps.production.models import ProductionBatch, HistoricalData
from decimal import Decimal

class Command(BaseCommand):
    help = 'Generate historical data from existing production batches'

    def handle(self, *args, **kwargs):
        batches = ProductionBatch.objects.all()
        for batch in batches:
            historical_data = HistoricalData(
                batch=batch,  # Set the foreign key to the ProductionBatch instance
                quantity_produced=batch.quantity_produced,
                quantity_rejected=batch.quantity_rejected,
                status=batch.status,
                selling_price=float(batch.schedule.product.selling_price) if hasattr(batch.schedule.product, 'selling_price') else 0.0,  # Convert to float
                production_date=batch.start_time.date(),
                quality_check_results=[
                    {
                        'check_date': qc.check_date.isoformat(),  # Convert datetime to string
                        'strength_test': float(qc.strength_test) if isinstance(qc.strength_test, Decimal) else qc.strength_test,  # Convert to float
                        'result': qc.result,
                    } for qc in batch.quality_checks.all()
                ],
            )
            historical_data.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully created historical data for batch {batch.batch_number}'))