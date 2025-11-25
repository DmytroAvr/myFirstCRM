# 8. MANAGEMENT COMMAND для масового оновлення
# oids/management/commands/update_trip_result_statuses.py

from django.core.management.base import BaseCommand
from oids.models import TripResultForUnit
class Command(BaseCommand):
    help = 'Оновлює статуси WorkRequestItem для всіх відправок у в/ч'

    def handle(self, *args, **options):
        trip_results = TripResultForUnit.objects.all()
        
        self.stdout.write(f"Found {trip_results.count()} trip results")
        
        for trip_result in trip_results:
            self.stdout.write(f"\nProcessing TripResult ID {trip_result.id}")
            trip_result.update_related_wri_statuses()
        
        self.stdout.write(self.style.SUCCESS('\n✅ All statuses updated!'))


# ВИКОРИСТАННЯ:
"""
# 1. У view після створення відправки:
trip_result.save()
update_statuses_after_sending_to_unit(trip_result)

# 2. У Django shell для тестування:
from oids.views import test_trip_result_status_update
test_trip_result_status_update(1)  # ID вашої відправки

# 3. Management command для масового оновлення:
python manage.py update_trip_result_statuses
"""