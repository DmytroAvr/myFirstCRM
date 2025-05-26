from oids.models import \*
from django.utils import timezone
import random

# === Територіальні управління ===

tus = [TerritorialManagement.objects.create(
code=f"ТУ-{i+1}",
name=f"Територіальне управління {i+1}",
note="Примітка до ТУ"
) for i in range(7)]

# === Групи військових частин ===

groups = [UnitGroup.objects.create(
name=f"Група частин {i+1}",
note="Примітка до групи"
) for i in range(7)]

# === Військові частини ===

units = []
for i in range(50):
unit = Unit.objects.create(
territorial_management=random.choice(tus),
code=f"ВЧ-{100+i}",
name=f"Військова частина {i+1}",
city=f"Місто {i+1}",
distance_from_gu=random.randint(10, 800),
note="Примітка до частини"
)
unit.unit_groups.set(random.sample(groups, k=random.randint(1, 3)))
units.append(unit)

# === Особи ===

people = [Person.objects.create(
full_name=f"Іваненко Іван {i+1}",
position="Аналітик",
is_active=random.choice([True, True, False])
) for i in range(10)]

# === ОІД ===

oids = []
for i in range(80):
oids.append(OID.objects.create(
unit=random.choice(units),
oid_type=random.choice(['МОВНА', 'ПЕМІН']),
cipher=f"ОІД-{i+1:03d}",
full_name=f"Об'єкт інформаційної діяльності {i+1}",
room=f"Кімната {i+10}",
status=random.choice([choice[0] for choice in OIDStatusChoices.choices]),
note="Примітка до ОІД"
))

# === Типи документів ===

doc_types = [DocumentType.objects.create(
oid_type=random.choice(['МОВНА', 'ПЕМІН']),
work_type=random.choice(['Атестація', 'ІК']),
name=f"Тип документу {i+1}",
has_expiration=random.choice([True, False]),
duration_months=random.choice([0, 6, 12]),
is_required=True
) for i in range(7)]

# === Заявки ===

requests = [WorkRequest.objects.create(
unit=random.choice(units),
incoming_number=f"Заявка-{i+1}",
incoming_date=timezone.now().date(),
note="Примітка до заявки",
status=random.choice([choice[0] for choice in WorkRequestStatusChoices.choices])
) for i in range(7)]

# === Елементи заявок ===

items = []
for req in requests:
for i in range(2):
items.append(WorkRequestItem.objects.create(
request=req,
oid=random.choice(oids),
work_type=random.choice(['Атестація', 'ІК']),
status=random.choice([choice[0] for choice in WorkRequestStatusChoices.choices])
))

# === Документи ===

docs = []
for i, item in enumerate(items[:10]):
doc = Document.objects.create(
oid=item.oid,
work_request_item=item,
document_type=random.choice(doc_types),
document_number=f"Д-{i+1}/14",
process_date=timezone.now().date(),
work_date=timezone.now().date(),
author=random.choice(people),
note="Автоматично створений документ"
)
docs.append(doc)

# === Відрядження ===

trips = []
for i in range(7):
trip = Trip.objects.create(
start_date=timezone.now().date(),
end_date=timezone.now().date(),
purpose="Мета поїздки"
)
trip.units.set(random.sample(units, 2))
trip.oids.set(random.sample(oids, 2))
trip.persons.set(random.sample(people, 2))
trip.work_requests.set(random.sample(requests, 2))
trips.append(trip)

# === Зміни статусів ОІД ===

for i in range(10):
OIDStatusChange.objects.create(
oid=random.choice(oids),
old_status="створюється",
new_status=random.choice([choice[0] for choice in OIDStatusChoices.choices if choice[0] != 'створюється']),
initiating_document=random.choice(docs),
reason="Зміна статусу для тесту",
changed_by=random.choice(people)
)

print("✅ Усі тестові дані успішно створені.")
