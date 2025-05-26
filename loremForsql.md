python manage.py shell

from oids.models import *
from django.utils import timezone
import random

# Територіальні управління
tus = [TerritorialManagement.objects.create(code=f"ТУ-{i+1}", name=f"ТерУпр {i+1}") for i in range(3)]

# Військові частини
units = [
    Unit.objects.create(
        territorial_management=random.choice(tus),
        code=f"ВЧ-{100+i}",
        name=f"Військова частина {i+1}",
        city=f"Місто {i+1}",
        distance_from_gu=random.randint(10, 500)
    ) for i in range(15)
]

# Групи військових частин
groups = [UnitGroup.objects.create(name=f"Група {i+1}") for i in range(5)]
for unit in units:
    unit.unit_groups.set(random.sample(groups, k=random.randint(1, len(groups))))

# Виконавці
people = [Person.objects.create(full_name=f"Особа {i+1}", position="Аналітик") for i in range(4)]

# ОІД
oids = [
    OID.objects.create(
        unit=random.choice(units),
        oid_type=random.choice(['МОВНА', 'ПЕМІН']),
        cipher=f"ОІД-{i+1}",
        full_name=f"Об'єкт №{i+1}",
        room=f"Кімната {100+i}",
        status=random.choice(OIDStatusChoices.values)
    ) for i in range(30)
]

# Типи документів
doc_types = [
    DocumentType.objects.create(
        oid_type=random.choice(['МОВНА', 'ПЕМІН']),
        work_type=random.choice(['Атестація', 'ІК']),
        name=f"Тип документу {i+1}",
        has_expiration=random.choice([True, False]),
        duration_months=random.choice([0, 6, 12]),
        is_required=True
    ) for i in range(5)
]

# Заявки
requests = [
    WorkRequest.objects.create(
        unit=random.choice(units),
        incoming_number=f"WR-{i+1}",
        note=f"Примітка до заявки {i+1}",
        status=random.choice(WorkRequestStatusChoices.values)
    ) for i in range(30)
]

# Елементи заявок
wri = []
for req in requests:
    for i in range(3):
        wri.append(
            WorkRequestItem.objects.create(
                request=req,
                oid=random.choice(oids),
                work_type=random.choice(['Атестація', 'ІК']),
                status=random.choice(WorkRequestStatusChoices.values)
            )
        )

# Документи
docs = [
    Document.objects.create(
        oid=wr.oid,
        work_request_item=wr,
        document_type=random.choice(doc_types),
        document_number=f"Д-{i+1}/14",
        process_date=timezone.now().date(),
        work_date=timezone.now().date(),
        author=random.choice(people),
        note="Тестовий документ"
    ) for i, wr in enumerate(wri[:5])
]

# Відрядження
trips = []
for i in range(10):
    trip = Trip.objects.create(
        start_date=timezone.now().date(),
        end_date=timezone.now().date(),
        purpose="Тестова мета"
    )
    trip.units.set(random.sample(units, 2))
    trip.oids.set(random.sample(oids, 2))
    trip.persons.set(random.sample(people, 2))
    trip.work_requests.set(requests)
    trips.append(trip)

# Технічні завдання
for i in range(20):
    TechnicalTask.objects.create(
        oid=random.choice(oids),
        input_number=f"ТЗ-{i+1}",
        input_date=timezone.now().date(),
        reviewed_by=random.choice(people),
        review_result=random.choice(DocumentReviewResultChoices.values),
        note="Примітка"
    )

# Реєстрація атестацій
regs = [
    AttestationRegistration.objects.create(
        process_date=timezone.now().date(),
        registration_number=f"Акт-{i+1}",
        note="Тест"
    ) for i in range(20)
]
for reg in regs:
    reg.units.set(units[:2])

# Відповіді на атестацію
for reg in regs:
    AttestationResponse.objects.create(
        registration=reg,
        registered_number=f"Відповідь-{reg.id}",
        registered_date=timezone.now().date(),
        note="Все добре"
    )

# Акти атестації
for reg in regs:
    doc = random.choice(docs)
    AttestationItem.objects.create(
        registration=reg,
        oid=doc.oid,
        document=doc
    )

# Зміни статусу ОІД
for oid in oids[:3]:
    OIDStatusChange.objects.create(
        oid=oid,
        old_status=OIDStatusChoices.NEW,
        new_status=OIDStatusChoices.ACTIVE,
        changed_by=random.choice(people),
        reason="Перехід до активної фази"
    )

# Результати відряджень
for i in range(5):
    tr = TripResultForUnit.objects.create(
        trip=random.choice(trips),
        process_date=timezone.now().date(),
        note="Результати передані"
    )
    tr.units.set(units[:5])
    tr.oids.set(oids[:5])
    tr.documents.set(docs[:5])

print("✅ Тестові дані успішно створено.")
