# oids/management/commands/populate_data.py
# python manage.py populate_data
import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from oids.models import (PeminSubTypeChoices, OIDStatusChoices, WorkRequestStatusChoices,
                        SecLevelChoices, WorkTypeChoices,  OIDTypeChoices, )
from oids.models import (
    TerritorialManagement, UnitGroup, Unit, Person,
    OID, DocumentType, WorkRequest, WorkRequestItem, 
    Document,
    # Додайте інші моделі, якщо їх також потрібно заповнити
    # AttestationRegistration, Trip, TechnicalTask
)

class Command(BaseCommand):
    help = 'Заповнює базу даних початковими тестовими даними для додатку OID.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Починаємо процес заповнення бази даних...")

        # Видалення старих даних для чистого заповнення (опційно)
        # Увага: це видалить ВСІ дані з цих моделей!
        # Document.objects.all().delete()
        # WorkRequestItem.objects.all().delete()
        # WorkRequest.objects.all().delete()
        # OID.objects.all().delete()
        # Unit.objects.all().delete()
        # TerritorialManagement.objects.all().delete()
        # Person.objects.all().delete()
        # DocumentType.objects.all().delete()
        # self.stdout.write(self.style.WARNING('Старі дані було видалено.'))
        
        # Виклик функцій для створення даних у правильному порядку залежностей
        self._create_document_types()
        self._create_persons()
        self._create_territorial_managements_and_units()
        self._create_oids()
        self._create_work_requests_and_items()
        self._create_documents()

        self.stdout.write(self.style.SUCCESS("Процес заповнення бази даних успішно завершено!"))

    def _create_document_types(self):
        self.stdout.write("Створення типів документів...")

        # --- Ключові документи для логіки зміни статусу WRI ---
        DocumentType.objects.get_or_create( 
            name="Акт атестації комплексу ТЗІ",
            oid_type='СПІЛЬНИЙ',
            work_type=WorkTypeChoices.ATTESTATION,
            defaults={'has_expiration': True, 'duration_months': 60}
        )
        DocumentType.objects.get_or_create(
            name="Висновок ІК",
            oid_type='СПІЛЬНИЙ',
            work_type='СПІЛЬНИЙ',
            defaults={'has_expiration': True, 'duration_months': 20}
        )
        # --- Інші документи ---
        DocumentType.objects.get_or_create(
            name="Програма та методика атестації",
            oid_type='СПІЛЬНИЙ',
            work_type=WorkTypeChoices.ATTESTATION,
            defaults={'has_expiration': False}
        )
        DocumentType.objects.get_or_create(
            name="Протокол ІК",
            oid_type='СПІЛЬНИЙ',
            work_type='СПІЛЬНИЙ', # Спільний для Атестації та ІК
            defaults={'has_expiration': False}
        )
        DocumentType.objects.get_or_create(
            name="Припис на експлуатацію",
            oid_type='СПІЛЬНИЙ',
            work_type=WorkTypeChoices.ATTESTATION,
            defaults={'has_expiration': True, 'duration_months': 60} # Приклад
        )
        self.stdout.write(self.style.SUCCESS("Типи документів створено."))


    def _create_persons(self):
        self.stdout.write("Створення виконавців (осіб)...")
        Person.objects.get_or_create(
            full_name="Петренко Петро Петрович",
            defaults={'position': 'Старший інженер', 'is_active': True}
        )
        Person.objects.get_or_create(
            full_name="Іваненко Іван Іванович",
            defaults={'position': 'Начальник відділу', 'is_active': True}
        )
        Person.objects.get_or_create(
            full_name="Сидоренко Сидір Сидорович",
            defaults={'position': 'Інженер', 'is_active': False}
        )
        self.stdout.write(self.style.SUCCESS("Виконавців створено."))

    def _create_territorial_managements_and_units(self):
        self.stdout.write("Створення територіальних управлінь та військових частин...")
        
        # Територіальні управління
        tu_center, _ = TerritorialManagement.objects.get_or_create(
            code="TU_CENTER", defaults={'name': 'Центральне територіальне управління'}
        )
        tu_west, _ = TerritorialManagement.objects.get_or_create(
            code="TU_WEST", defaults={'name': 'Західне територіальне управління'}
        )

        # Групи частин
        group_kyiv, _ = UnitGroup.objects.get_or_create(name="Київський гарнізон")

        # Військові частини
        unit_3030, _ = Unit.objects.get_or_create(
            code="3030",
            defaults={
                'name': '101-ша окрема бригада охорони ГШ',
                'city': 'Київ',
                'distance_from_gu': 10,
                'territorial_management': tu_center
            }
        )
        unit_2269, _ = Unit.objects.get_or_create(
            code="2269",
            defaults={
                'name': '1-ша окрема танкова сіверська бригада',
                'city': 'смт Гончарівське',
                'distance_from_gu': 150,
                'territorial_management': tu_center
            }
        )
        unit_2240, _ = Unit.objects.get_or_create(
            code="2240",
            defaults={
                'name': '24-та окрема механізована бригада',
                'city': 'м. Яворів',
                'distance_from_gu': 550,
                'territorial_management': tu_west
            }
        )

        # Додавання частини до групи
        unit_3030.unit_groups.add(group_kyiv)

        self.stdout.write(self.style.SUCCESS("Територіальні управління та військові частини створено."))

    def _create_oids(self):
        self.stdout.write("Створення об'єктів інформаційної діяльності (ОІД)...")
        
        unit_3030 = Unit.objects.get(code="3030")
        unit_2240 = Unit.objects.get(code="2240")

        OID.objects.get_or_create(
            cipher="101/01-ПЕМІН",
            unit=unit_3030,
            defaults={
                'oid_type': OIDTypeChoices.PEMIN,
                'pemin_sub_type': PeminSubTypeChoices.AS1_23PORTABLE,
                'serial_number': 'E325333',
                'full_name': 'Автоматизоване робоче місце оперативного чергового',
                'room': 'к. 112',
                'status': OIDStatusChoices.ACTIVE,
                'sec_level': SecLevelChoices.S
            }
        )
        OID.objects.get_or_create(
            cipher="101/02-МОВНА",
            unit=unit_3030,
            defaults={
                'oid_type': OIDTypeChoices.SPEAK,
                'pemin_sub_type': PeminSubTypeChoices.SPEAKSUBTYPE,
                'full_name': 'Кімната для переговорів командування',
                'room': 'к. 205',
                'status': OIDStatusChoices.ACTIVE,
                'sec_level': SecLevelChoices.TS
            }
        )
        OID.objects.get_or_create(
            cipher="284/01-ПЕМІН",
            unit=unit_2240,
            defaults={
                'oid_type': OIDTypeChoices.PEMIN,
                'pemin_sub_type': PeminSubTypeChoices.VARM,
                'serial_number': '654555',
                'full_name': 'Захищений комп\'ютер штабу',
                'room': 'к. 3, буд. 5',
                'status': OIDStatusChoices.RECEIVED_REQUEST,
                'sec_level': SecLevelChoices.TS
            }
        )
        self.stdout.write(self.style.SUCCESS("ОІД створено."))

    def _create_work_requests_and_items(self):
        self.stdout.write("Створення заявок на проведення робіт та їх елементів...")

        # Отримання даних, створених раніше
        unit_3030 = Unit.objects.get(code="3030")
        oid_pemin_101 = OID.objects.get(cipher="101/01-ПЕМІН")
        oid_movna_101 = OID.objects.get(cipher="101/02-МОВНА")

        # --- Заявка 1: на атестацію та ІК для ВЧ 3030 ---
        wr1, created = WorkRequest.objects.get_or_create(
            unit=unit_3030,
            incoming_number="123/4/567",
            defaults={
                'incoming_date': datetime.date(2025, 5, 10),
                'status': WorkRequestStatusChoices.PENDING,
                'note': 'Прохання провести роботи у червні.'
            }
        )
        
        if created:
            WorkRequestItem.objects.create(
                request=wr1,
                oid=oid_pemin_101,
                work_type=WorkTypeChoices.ATTESTATION
            )
            WorkRequestItem.objects.create(
                request=wr1,
                oid=oid_pemin_101, # Той самий ОІД, але інший тип робіт
                work_type=WorkTypeChoices.IK
            )
        
        # --- Заявка 2: тільки на атестацію МОВНА для ВЧ 3030 ---
        wr2, created = WorkRequest.objects.get_or_create(
            unit=unit_3030,
            incoming_number="123/4/888",
            defaults={
                'incoming_date': datetime.date(2025, 6, 1),
                'status': WorkRequestStatusChoices.IN_PROGRESS,
                'note': 'Термінова заявка.'
            }
        )
        if created:
             WorkRequestItem.objects.create(
                request=wr2,
                oid=oid_movna_101,
                work_type=WorkTypeChoices.ATTESTATION
            )
            
        self.stdout.write(self.style.SUCCESS("Заявки на проведення робіт створено."))
    
    def _create_documents(self):
        self.stdout.write("Створення опрацьованих документів...")
        
        # Отримання даних, створених раніше
        oid_pemin_101 = OID.objects.get(cipher="101/01-ПЕМІН")
        wri_attestation = WorkRequestItem.objects.get(oid=oid_pemin_101, work_type=WorkTypeChoices.ATTESTATION)
        wri_ik = WorkRequestItem.objects.get(oid=oid_pemin_101, work_type=WorkTypeChoices.IK)
        
        doc_type_act = DocumentType.objects.get(name="Акт атестації комплексу ТЗІ")
        doc_type_conclusion = DocumentType.objects.get(name="Висновок ІК")
        
        person_petrenko = Person.objects.get(full_name__startswith="Петренко")

        # --- Створення Акту атестації (без реєстраційних даних) ---
        # Це симулює реальний процес: спочатку створюється акт, а потім він реєструється.
        Document.objects.get_or_create(
            document_number='27/14-1111',
            document_type=doc_type_act,
            oid=oid_pemin_101,
            defaults={
                'work_request_item': wri_attestation,
                'process_date': datetime.date(2025, 6, 20),
                'work_date': datetime.date(2025, 6, 15),
                'author': person_petrenko,
                'note': 'Акт підготовлено, очікує відправки на реєстрацію.'
                # dsszzi_registered_number та dsszzi_registered_date залишаються порожніми
            }
        )

        # --- Створення Висновку ІК ---
        # Для цього документа достатньо його існування, щоб змінити статус WRI на COMPLETED.
        Document.objects.get_or_create(
            document_number='27/14-2222',
            document_type=doc_type_conclusion,
            oid=oid_pemin_101,
            defaults={
                'work_request_item': wri_ik,
                'process_date': datetime.date(2025, 6, 21),
                'work_date': datetime.date(2025, 6, 15),
                'author': person_petrenko,
                'note': 'Висновок підготовлено.'
            }
        )
        
        self.stdout.write(self.style.SUCCESS("Опрацьовані документи створено."))