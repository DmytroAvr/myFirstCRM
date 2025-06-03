import os
import django
import datetime
from django.utils import timezone

# Налаштування Django оточення
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myProject.settings') # ЗАМІНІТЬ 'myProject' на назву вашого проекту
django.setup()

from oids.models import (
    TerritorialManagement, UnitGroup, Unit, OID, Person, WorkRequest, WorkRequestItem,
    DocumentType, Document, Trip, OIDStatusChange, AttestationRegistration, 
    AttestationResponse, TripResultForUnit, TechnicalTask,
    SecLevelChoices, OIDStatusChoices, WorkRequestStatusChoices, OIDTypeChoices,
    WorkTypeChoices, DocumentReviewResultChoices, AttestationRegistrationStatusChoices
)

# Встановлюємо фіксовану дату для всіх полів дат
FIXED_DATE = datetime.date(2025, 5, 1)

def populate_data():
    print("Starting data population...")

    # 1. Person (Виконавці)
    # Створимо кількох осіб, якщо їх ще немає
    persons_data = [
        {"full_name": "Іванов Іван Іванович (Person)", "position": "Інженер (Position)"},
        {"full_name": "Петров Петро Петрович (Person)", "position": "Старший інженер (Position)"},
        {"full_name": "Сидоренко Сидір Сидорович (Person)", "position": "Начальник відділу (Position)"},
    ]
    created_persons = []
    for i, p_data in enumerate(persons_data):
        person, created = Person.objects.get_or_create(
            full_name=f"{p_data['full_name']} {i+1}", # Додаємо унікальність
            defaults={'position': p_data['position'], 'is_active': True}
        )
        if created:
            print(f"Created Person: {person.full_name}")
        created_persons.append(person)
    
    person1 = Person.objects.first()
    if not person1 and created_persons:
        person1 = created_persons[0]
    elif not person1:
        print("ERROR: No Person found or created. Cannot proceed with dependent models.")
        return

    # 2. DocumentType (Типи документів)
    # Створимо кілька типів документів, якщо їх ще немає
    doc_types_data = [
        {"name": "Акт атестації (DocumentType Name)", "oid_type": "СПІЛЬНИЙ", "work_type": "Атестація", "has_expiration": True, "duration_months": 60, "is_required": True},
        {"name": "Висновок ІК (DocumentType Name)", "oid_type": "СПІЛЬНИЙ", "work_type": "ІК", "has_expiration": True, "duration_months": 20, "is_required": True},
        {"name": "Припис на експлуатацію (DocumentType Name)", "oid_type": "СПІЛЬНИЙ", "work_type": "Атестація", "has_expiration": True, "duration_months": 60, "is_required": False},
        {"name": "План пошуку ЗП (DocumentType Name)", "oid_type": "СПІЛЬНИЙ", "work_type": "СПІЛЬНИЙ", "is_required": True},
        {"name": "Протокол огляду (DocumentType Name)", "oid_type": "ПЕМІН", "work_type": "Атестація", "is_required": False},
    ]
    created_doc_types = []
    for i, dt_data in enumerate(doc_types_data):
        doc_type, created = DocumentType.objects.get_or_create(
            name=dt_data['name'],
            oid_type=dt_data['oid_type'],
            work_type=dt_data['work_type'],
            defaults={
                'has_expiration': dt_data.get('has_expiration', False),
                'duration_months': dt_data.get('duration_months', 0),
                'is_required': dt_data.get('is_required', True)
            }
        )
        if created:
            print(f"Created DocumentType: {doc_type.name}")
        created_doc_types.append(doc_type)

    doc_type_act = DocumentType.objects.filter(name__icontains="Акт атестації").first()
    doc_type_conclusion = DocumentType.objects.filter(name__icontains="Висновок ІК").first()
    if not doc_type_act and created_doc_types: doc_type_act = created_doc_types[0]
    if not doc_type_conclusion and len(created_doc_types) > 1: doc_type_conclusion = created_doc_types[1]
    
    if not doc_type_act:
        print("ERROR: No 'Акт атестації' DocumentType found or created. Cannot proceed fully.")
        # return # Можна зупинити, якщо це критично

    # Припускаємо, що Unit та OID вже існують (створені main_unit_data.py або іншим скриптом)
    # Якщо ні, потрібно їх створити тут або переконатися, що вони є.
    # Для прикладу, візьмемо перші доступні Unit та OID
    unit1 = Unit.objects.first()
    if not unit1:
        # Створимо тестову ВЧ, якщо немає
        tm1, _ = TerritorialManagement.objects.get_or_create(code="00", defaults={'name': "ТУ Тест (TerritorialManagement Name)"})
        unit1, _ = Unit.objects.get_or_create(code="00000", defaults={'territorial_management': tm1, 'city': "Тест Місто (City)"})
        print(f"Created default Unit: {unit1.code}")

    oid1 = OID.objects.filter(unit=unit1).first()
    if not oid1:
        oid1, _ = OID.objects.get_or_create(
            cipher=f"TESTOID001-{unit1.code}",
            defaults={
                'unit': unit1,
                'oid_type': OIDTypeChoices.PEMIN,
                'sec_level': SecLevelChoices.DSK,
                'full_name': "Тестовий ОІД 1 (Full Name)",
                'room': "Кімн. 101 (Room)",
                'status': OIDStatusChoices.NEW,
            }
        )
        print(f"Created default OID: {oid1.cipher}")

    oid2 = OID.objects.filter(unit=unit1, oid_type=OIDTypeChoices.SPEAK).first()
    if not oid2 and OID.objects.count() < 2 : # Створимо другий ОІД іншого типу, якщо його немає
         oid2, _ = OID.objects.get_or_create(
            cipher=f"TESTOID002SPEAK-{unit1.code}",
            defaults={
                'unit': unit1,
                'oid_type': OIDTypeChoices.SPEAK,
                'sec_level': SecLevelChoices.S,
                'full_name': "Тестовий ОІД 2 МОВНА (Full Name)",
                'room': "Кімн. 102 (Room)",
                'status': OIDStatusChoices.NEW,
            }
        )
         print(f"Created default OID: {oid2.cipher}")
    elif not oid2 and OID.objects.exclude(pk=oid1.pk).exists():
        oid2 = OID.objects.exclude(pk=oid1.pk).first()


    # 3. WorkRequest (Заявки)
    wr1, created = WorkRequest.objects.get_or_create(
        unit=unit1,
        incoming_number="WR-001/25",
        defaults={
            'incoming_date': FIXED_DATE,
            'note': "Примітка для Заявки WR-001/25 (Note)",
            'status': WorkRequestStatusChoices.PENDING
        }
    )
    if created: print(f"Created WorkRequest: {wr1}")

    # 4. WorkRequestItem (Елементи Заявок)
    if oid1:
        wri1, created = WorkRequestItem.objects.get_or_create(
            request=wr1,
            oid=oid1,
            work_type=WorkTypeChoices.ATTESTATION,
            defaults={'status': WorkRequestStatusChoices.PENDING}
        )
        if created: print(f"Created WorkRequestItem: {wri1}")
    
    if oid2:
        wri2, created = WorkRequestItem.objects.get_or_create(
            request=wr1,
            oid=oid2,
            work_type=WorkTypeChoices.IK,
            defaults={'status': WorkRequestStatusChoices.PENDING}
        )
        if created: print(f"Created WorkRequestItem: {wri2}")

    # 5. TechnicalTask (Технічні Завдання)
    if oid1:
        tt1, created = TechnicalTask.objects.get_or_create(
            oid=oid1,
            input_number="ТЗ-ВХ-001",
            defaults={
                'input_date': FIXED_DATE,
                'read_till_date': FIXED_DATE + datetime.timedelta(days=30),
                'review_result': DocumentReviewResultChoices.READ, # Статус "Опрацювати"
                'note': "Примітка для Технічного Завдання ТЗ-ВХ-001 (Note)",
                'reviewed_by': person1 
            }
        )
        if created: print(f"Created TechnicalTask: {tt1}")

    # 6. Document (Документи)
    if oid1 and doc_type_act and wri1: # Перевіряємо наявність wri1
        doc1, created = Document.objects.get_or_create(
            oid=oid1,
            document_type=doc_type_act, # Акт атестації
            document_number=f"27/14-АА-{oid1.cipher}",
            defaults={
                'work_request_item': wri1,
                'process_date': FIXED_DATE,
                'work_date': FIXED_DATE - datetime.timedelta(days=5), # Роботи були раніше
                'author': person1,
                'note': "Примітка для Документа Акт Атестації (Note)",
            }
        )
        if created: print(f"Created Document: {doc1}")

    if oid2 and doc_type_conclusion and wri2: # Перевіряємо наявність wri2
        doc2, created = Document.objects.get_or_create(
            oid=oid2,
            document_type=doc_type_conclusion, # Висновок ІК
            document_number=f"27/14-ВІК-{oid2.cipher}",
            defaults={
                'work_request_item': wri2,
                'process_date': FIXED_DATE,
                'work_date': FIXED_DATE - datetime.timedelta(days=3),
                'author': person1,
                'note': "Примітка для Документа Висновок ІК (Note)",
            }
        )
        if created: print(f"Created Document: {doc2}")

    # 7. Trip (Відрядження)
    trip1, created = Trip.objects.get_or_create(
        purpose="Мета: Проведення атестації та ІК (Purpose)",
        defaults={
            'start_date': FIXED_DATE - datetime.timedelta(days=10),
            'end_date': FIXED_DATE - datetime.timedelta(days=7) # Відрядження завершилося
        }
    )
    if created:
        trip1.units.add(unit1)
        if oid1: trip1.oids.add(oid1)
        if oid2: trip1.oids.add(oid2)
        if person1: trip1.persons.add(person1)
        trip1.work_requests.add(wr1) # Пов'язуємо з заявкою
        print(f"Created Trip: {trip1} and associated M2M")

    # 8. AttestationRegistration (Відправка Актів на реєстрацію)
    # Створюємо, якщо є документ типу "Акт атестації" (doc1) і він ще не відправлений
    if 'doc1' in locals() and doc1 and doc1.attestation_registration_sent is None:
        att_reg1, created = AttestationRegistration.objects.get_or_create(
            outgoing_letter_number="ВИХ-ДССЗЗІ-001",
            defaults={
                'outgoing_letter_date': FIXED_DATE,
                'sent_by': person1,
                'status': AttestationRegistrationStatusChoices.SENT,
                'note': "Примітка до Відправки Актів Атестації (Note)"
            }
        )
        if created:
            att_reg1.units.add(doc1.oid.unit) # Додаємо ВЧ документа
            # Оновлюємо документ, пов'язуючи його з цією відправкою
            doc1.attestation_registration_sent = att_reg1
            doc1.save(update_fields=['attestation_registration_sent'])
            print(f"Created AttestationRegistration: {att_reg1} and linked Document ID {doc1.id}")
    else:
        att_reg1 = AttestationRegistration.objects.filter(outgoing_letter_number="ВИХ-ДССЗЗІ-001").first()

    # 9. AttestationResponse (Відповідь на реєстрацію)
    # Створюємо, якщо є відправка (att_reg1) і для неї ще немає відповіді
    if att_reg1 and not hasattr(att_reg1, 'response_received'):
        att_resp1, created = AttestationResponse.objects.get_or_create(
            attestation_registration_sent=att_reg1,
            defaults={
                'response_letter_number': "ВХ-ДССЗЗІ-001- відповідь",
                'response_letter_date': FIXED_DATE + datetime.timedelta(days=10),
                'received_by': person1,
                'note': "Примітка до Відповіді ДССЗЗІ (Note)"
            }
        )
        if created:
            print(f"Created AttestationResponse: {att_resp1}")
            # Оновлюємо документ реєстраційними даними
            if 'doc1' in locals() and doc1 and doc1.attestation_registration_sent == att_reg1:
                doc1.dsszzi_registered_number = f"ДССЗЗІ-REG-{doc1.id}"
                doc1.dsszzi_registered_date = FIXED_DATE + datetime.timedelta(days=9)
                doc1.save(update_fields=['dsszzi_registered_number', 'dsszzi_registered_date'])
                print(f"Updated Document ID {doc1.id} with DSSZZI registration data.")
    
    # 10. TripResultForUnit (Результати відрядження для ВЧ)
    # Створюємо, якщо є відрядження (trip1) та документи (doc1, doc2)
    if trip1 and 'doc1' in locals() and doc1:
        trfu1, created = TripResultForUnit.objects.get_or_create(
            trip=trip1,
            process_date=FIXED_DATE + datetime.timedelta(days=1), # Дата відправки до частини
            defaults={
                'note': "Примітка до Результатів відрядження для ВЧ (Note)",
                'outgoing_letter_number': f"СУПРОВІД-{unit1.code}-{trip1.id}", # Генеруємо унікальний номер
                'outgoing_letter_date': FIXED_DATE + datetime.timedelta(days=1)
            }
        )
        if created:
            trfu1.units.add(unit1)
            trfu1.oids.add(oid1)
            trfu1.documents.add(doc1)
            if 'doc2' in locals() and doc2: # Якщо є другий документ
                trfu1.oids.add(oid2)
                trfu1.documents.add(doc2)
            print(f"Created TripResultForUnit: {trfu1} and associated M2M")
            # Після створення TripResultForUnit, метод Trip.save() має спрацювати (якщо викликається з форми)
            # або сигнал для Trip, щоб оновити doc_processing_deadline для WorkRequestItems.
            # Якщо ця логіка у вас в save() TripResultForUnit, то вона спрацює тут.
            # Якщо ви перенесли логіку в сигнал для Trip, то вона мала спрацювати раніше при збереженні Trip.

    # 11. OIDStatusChange (Історія змін статусу ОІД)
    # Ця модель зазвичай заповнюється автоматично при зміні статусу OID
    # Але для прикладу можна створити запис
    if oid1 and oid1.status != OIDStatusChoices.ACTIVE:
        old_status_for_change = oid1.status
        oid1.status = OIDStatusChoices.ACTIVE # Припустимо, він став активним
        oid1.save(update_fields=['status']) # Це має створити запис OIDStatusChange, якщо є відповідний сигнал або логіка в save() OID
                                            # Або створюємо його тут вручну, якщо такої логіки немає
        change, created = OIDStatusChange.objects.get_or_create(
            oid=oid1,
            old_status=old_status_for_change,
            new_status=OIDStatusChoices.ACTIVE,
            defaults={
                'reason': "Статус змінено на Активний після додавання тестових даних (Reason)",
                'changed_by': person1,
                # 'initiating_document': doc1 (якщо doc1 - причина)
            }
        )
        if created: print(f"Created OIDStatusChange: {change}")


    print("Data population script finished.")

if __name__ == '__main__':
    populate_data()