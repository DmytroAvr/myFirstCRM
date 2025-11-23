# populate_all_models.py
import os
import django
import datetime
import random
from django.utils import timezone

# Налаштування Django оточення
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oids.settings')
django.setup()

from oids.models import (
    TerritorialManagement, UnitGroup, Unit, OID, Person, WorkRequest, WorkRequestItem,
    DocumentType, Document, Trip, OIDStatusChange, AttestationRegistration,
    AttestationResponse, TripResultForUnit, TechnicalTask,
    SecLevelChoices, OIDStatusChoices, WorkRequestStatusChoices, OIDTypeChoices,
    WorkTypeChoices, DocumentReviewResultChoices, AttestationRegistrationStatusChoices
)

FIXED_DATE = datetime.date(2025, 5, 1)

def get_or_create_person(i):
    full_name = f"Співробітник №{i}"
    position = f"Посада №{i}"
    person, created = Person.objects.get_or_create(
        full_name=full_name,
        defaults={'position': position}
    )
    if created:
        print(f"Created Person: {person.full_name}")
    return person

def get_or_create_doc_type(name_prefix, oid_type, work_type, duration=0, is_required=True):
    name = f"{name_prefix} (тип {oid_type}/{work_type})"
    doc_type, created = DocumentType.objects.get_or_create(
        name=name,
        oid_type=oid_type,
        work_type=work_type,
        defaults={
            'has_expiration': duration > 0,
            'duration_months': duration,
            'is_required': is_required
        }
    )
    if created:
        print(f"Created DocumentType: {doc_type.name}")
    return doc_type

def populate_all():
    print("--- Starting data population ---")

    # --- 1. Створення базових довідників ---
    print("\n--- Populating Base Directories (Person, DocumentType) ---")
    persons = [get_or_create_person(i) for i in range(1, 6)]
    main_person = persons[0]

    # Створюємо базові типи документів
    doc_type_att_act = get_or_create_doc_type("Акт атестації", "СПІЛЬНИЙ", "Атестація", 60)
    doc_type_ik_conc = get_or_create_doc_type("Висновок ІК", "СПІЛЬНИЙ", "ІК", 20)
    doc_type_plan = get_or_create_doc_type("План робіт", "СПІЛЬНИЙ", "СПІЛЬНИЙ", 0, False)
    doc_type_protocol = get_or_create_doc_type("Протокол", "СПІЛЬНИЙ", "СПІЛЬНИЙ", 0, False)

    # Припускаємо, що TerritorialManagement та Unit вже створені (напр. з main_unit_data.py)
    # Якщо ні, створюємо тестові
    tm1, _ = TerritorialManagement.objects.get_or_create(code="01", defaults={'name': "Тестове ТУ 01"})
    unit1, _ = Unit.objects.get_or_create(code="A0001", defaults={'territorial_management': tm1, 'name': 'Тестова ВЧ-1', 'city': 'Київ'})
    unit2, _ = Unit.objects.get_or_create(code="B0002", defaults={'territorial_management': tm1, 'name': 'Тестова ВЧ-2', 'city': 'Львів'})
    units = [unit1, unit2]

    # --- 2. Створення ОІД ---
    print("\n--- Populating OIDs ---")
    created_oids = []
    for i in range(1, 6):
        unit = random.choice(units)
        oid_type = random.choice([OIDTypeChoices.PEMIN, OIDTypeChoices.SPEAK])
        oid, created = OID.objects.get_or_create(
            cipher=f"TEST-{unit.code}-{i:03}",
            defaults={
                'unit': unit,
                'oid_type': oid_type,
                'sec_level': SecLevelChoices.S,
                'full_name': f"Тестовий ОІД №{i} ({oid_type})",
                'room': f"Приміщення {100+i}",
                'status': OIDStatusChoices.NEW,
            }
        )
        if created:
            print(f"Created OID: {oid}")
        created_oids.append(oid)

    # --- 3. Створення Заявок та Елементів Заявок ---
    print("\n--- Populating WorkRequests and Items ---")
    created_wri = []
    for i in range(1, 6):
        unit = random.choice(units)
        wr, created = WorkRequest.objects.get_or_create(
            unit=unit,
            incoming_number=f"WR-IN-{i:03}",
            defaults={'incoming_date': FIXED_DATE - datetime.timedelta(days=i*10)}
        )
        if created: print(f"Created WorkRequest: {wr}")

        # Додаємо 1-2 елементи до кожної заявки
        oids_for_request = random.sample(created_oids, k=random.randint(1, 2))
        for oid_for_item in oids_for_request:
            work_type = random.choice([WorkTypeChoices.ATTESTATION, WorkTypeChoices.IK])
            wri, created = WorkRequestItem.objects.get_or_create(
                request=wr, oid=oid_for_item, work_type=work_type
            )
            if created: 
                print(f"  - Created WorkRequestItem: {wri}")
                created_wri.append(wri)

    # --- 4. Створення Технічних Завдань ---
    print("\n--- Populating TechnicalTasks ---")
    for i in range(1, 6):
        oid = random.choice(created_oids)
        tt, created = TechnicalTask.objects.get_or_create(
            oid=oid,
            input_number=f"TZ-IN-{i:03}",
            defaults={
                'input_date': FIXED_DATE - datetime.timedelta(days=i*5),
                'read_till_date': FIXED_DATE + datetime.timedelta(days=30-i),
                'review_result': DocumentReviewResultChoices.READ,
                'reviewed_by': random.choice(persons)
            }
        )
        if created: print(f"Created TechnicalTask: {tt}")

    # --- 5. Створення Відряджень ---
    print("\n--- Populating Trips ---")
    # Створимо відрядження для першої заявки
    if WorkRequest.objects.exists():
        first_wr = WorkRequest.objects.first()
        trip_units = list(first_wr.items.values_list('oid__unit', flat=True).distinct())
        trip_oids = list(first_wr.items.values_list('oid', flat=True).distinct())

        trip, created = Trip.objects.get_or_create(
            purpose=f"Відрядження по заявці №{first_wr.incoming_number}",
            defaults={
                'start_date': FIXED_DATE - datetime.timedelta(days=10),
                'end_date': FIXED_DATE - datetime.timedelta(days=5),
            }
        )
        if created:
            trip.units.set(Unit.objects.filter(id__in=trip_units))
            trip.oids.set(OID.objects.filter(id__in=trip_oids))
            trip.persons.set(random.sample(persons, k=2))
            trip.work_requests.add(first_wr)
            # При збереженні M2M спрацює сигнал (якщо налаштований) для встановлення дедлайнів WRI
            print(f"Created Trip: {trip} and associated M2M")

    # --- 6. Створення Документів ---
    print("\n--- Populating Documents ---")
    # Створимо по одному ключовому документу для перших кількох WRI
    if created_wri:
        for i, wri in enumerate(created_wri[:3]):
            doc_type_to_create = doc_type_att_act if wri.work_type == WorkTypeChoices.ATTESTATION else doc_type_ik_conc
            if not doc_type_to_create: continue
            
            doc, created = Document.objects.get_or_create(
                work_request_item=wri,
                document_type=doc_type_to_create,
                defaults={
                    'oid': wri.oid,
                    'document_number': f"27/14-{wri.work_type[:3]}-{i}",
                    'doc_process_date': FIXED_DATE,
                    'work_date': FIXED_DATE - datetime.timedelta(days=i),
                    'author': random.choice(persons)
                }
            )
            if created:
                print(f"Created Document: {doc}")
                # При збереженні цього документа має спрацювати Document.save() -> wri.check_and_update_status_based_on_documents()

    # --- 7. Створення Відправки на Реєстрацію (AttestationRegistration) ---
    print("\n--- Populating AttestationRegistrations ---")
    # Знаходимо акти атестації, які ще не відправлені
    acts_to_send = Document.objects.filter(
        document_type=doc_type_act,
        attestation_registration_sent__isnull=True
    )[:2] # Беремо перші 2 для прикладу

    if acts_to_send.exists():
        att_reg, created = AttestationRegistration.objects.get_or_create(
            outgoing_letter_number="REG-SENT-001",
            defaults={
                'outgoing_letter_date': FIXED_DATE,
                'sent_by': main_person,
                'status': AttestationRegistrationStatusChoices.SENT
            }
        )
        if created:
            print(f"Created AttestationRegistration: {att_reg}")
            # Зв'язуємо акти з цією відправкою
            units_involved = set()
            for act in acts_to_send:
                act.attestation_registration_sent = att_reg
                act.save(update_fields=['attestation_registration_sent'])
                units_involved.add(act.oid.unit)
            att_reg.units.set(list(units_involved))
            print(f"  - Linked {acts_to_send.count()} acts to this registration.")
    
    # --- 8. Створення Відповіді на реєстрацію (AttestationResponse) ---
    print("\n--- Populating AttestationResponses ---")
    # Знаходимо відправку зі статусом "Відправлено"
    reg_awaiting_response = AttestationRegistration.objects.filter(status=AttestationRegistrationStatusChoices.SENT).first()
    if reg_awaiting_response:
        resp, created = AttestationResponse.objects.get_or_create(
            attestation_registration_sent=reg_awaiting_response,
            defaults={
                'response_letter_number': "RESP-IN-001",
                'response_letter_date': FIXED_DATE + datetime.timedelta(days=15),
                'received_by': main_person
            }
        )
        if created:
            print(f"Created AttestationResponse: {resp}")
            # Оновлюємо документи реєстраційними даними (це має викликати оновлення статусу WRI)
            docs_in_registration = reg_awaiting_response.sent_documents.all()
            for doc in docs_in_registration:
                doc.dsszzi_registered_number = f"D-{doc.id}-{FIXED_DATE.year}"
                doc.dsszzi_registered_date = FIXED_DATE + datetime.timedelta(days=14)
                doc.save(update_fields=['dsszzi_registered_number', 'dsszzi_registered_date'])
                print(f"  - Updated document {doc.id} with registration data.")
    
    print("\n--- Data population script finished. ---")


if __name__ == '__main__':
    # Викликаємо головну функцію
    populate_all()