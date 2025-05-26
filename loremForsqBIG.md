from oids.models import \*
from django.utils import timezone
from datetime import timedelta
import random

# Базові дані

tus = [TerritorialManagement.objects.create(code=f"ТУ-{i+1}", name=f"Теруправління {i+1}") for i in range(5)]
groups = [UnitGroup.objects.create(name=f"Група {i+1}") for i in range(5)]
units = []
for i in range(15):
unit = Unit.objects.create(
territorial_management=random.choice(tus),
code=f"ВЧ-{100+i}",
name=f"Частина {i+1}",
city=f"Місто {i+1}",
distance_from_gu=random.randint(10, 500)
)
unit.unit_groups.set(random.sample(groups, random.randint(1, 3)))
units.append(unit)

people = [Person.objects.create(full_name=f"ПІБ-{i+1}", position="Інженер") for i in range(10)]

# DocumentType

doc_types = [
DocumentType.objects.create(
oid_type=random.choice(['МОВНА', 'ПЕМІН']),
work_type=random.choice(['Атестація', 'ІК']),
name=f"Тип документу {i+1}",
has_expiration=random.choice([True, False]),
duration_months=random.choice([0, 6, 12]),
is_required=True
) for i in range(10)
]

# 300 OID

oids = []
for i in range(300):
oids.append(OID.objects.create(
unit=random.choice(units),
oid_type=random.choice(['МОВНА', 'ПЕМІН']),
cipher=f"ОІД-{i+1:04d}",
full_name=f"Об'єкт {i+1}",
room=f"{100+i}",
status=random.choice([choice[0] for choice in OIDStatusChoices.choices])
))

# 60 WorkRequest

requests = []
for i in range(60):
requests.append(WorkRequest.objects.create(
unit=random.choice(units),
incoming_number=f"WR-{i+1}",
incoming_date=timezone.now().date() - timedelta(days=random.randint(1, 100)),
note="Автоматично створено",
status=random.choice([choice[0] for choice in WorkRequestStatusChoices.choices])
))

# WorkRequestItems (2–5 на кожну заявку)

items = []
for req in requests:
for \_ in range(random.randint(2, 5)):
items.append(WorkRequestItem.objects.create(
request=req,
oid=random.choice(oids),
work_type=random.choice(['Атестація', 'ІК']),
status=random.choice([choice[0] for choice in WorkRequestStatusChoices.choices])
))

# 600 Document

docs = []
for i in range(600):
item = random.choice(items)
doc = Document.objects.create(
oid=item.oid,
work_request_item=item,
document_type=random.choice(doc_types),
document_number=f"Д-{i+1}/14",
process_date=timezone.now().date() - timedelta(days=random.randint(1, 60)),
work_date=timezone.now().date() - timedelta(days=random.randint(1, 60)),
author=random.choice(people),
note="Автогенерація"
)
docs.append(doc)

# 100 TechnicalTask

for i in range(100):
TechnicalTask.objects.create(
oid=random.choice(oids),
input_number=f"ТЗ-{i+1}",
input_date=timezone.now().date() - timedelta(days=random.randint(1, 90)),
reviewed_by=random.choice(people),
review_result=random.choice([choice[0] for choice in DocumentReviewResultChoices.choices]),
note="Автотест"
)

# 30 Trip (з випадковими датами)

trips = []
for i in range(30):
start = timezone.now().date() - timedelta(days=random.randint(10, 100))
end = start + timedelta(days=random.randint(1, 5))
trip = Trip.objects.create(
start_date=start,
end_date=end,
purpose="Автовідрядження"
)
trip.units.set(random.sample(units, 2))
trip.oids.set(random.sample(oids, 3))
trip.persons.set(random.sample(people, 2))
trip.work_requests.set(random.sample(requests, 2))
trips.append(trip)

# 50 OIDStatusChange

for i in range(50):
oid = random.choice(oids)
OIDStatusChange.objects.create(
oid=oid,
old_status=OIDStatusChoices.NEW,
new_status=random.choice([OIDStatusChoices.ACTIVE, OIDStatusChoices.TERMINATED, OIDStatusChoices.CANCELED]),
initiating_document=random.choice(docs),
reason="Авто зміна статусу",
changed_by=random.choice(people)
)

print("✅ Масові тестові дані успішно створені!")
