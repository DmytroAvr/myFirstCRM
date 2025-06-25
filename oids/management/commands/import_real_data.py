import csv
import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from oids.models import (
    TerritorialManagement, Unit, Person, DocumentType, OID,
    WorkRequest, WorkRequestItem, Document
)

class Command(BaseCommand):
    help = 'Імпортує реальні дані з CSV файлів у базу даних.'

    def add_arguments(self, parser):
        # Додаємо аргументи для шляхів до всіх файлів
        parser.add_argument('realdata/tu_csv', type=str, help='Шлях до CSV з ТУ')
        parser.add_argument('realdata/units_csv', type=str, help='Шлях до CSV з ВЧ')
        parser.add_argument('realdata/persons_csv', type=str, help='Шлях до CSV з виконавцями')
        parser.add_argument('realdata/doc_types_csv', type=str, help='Шлях до CSV з типами документів')
        parser.add_argument('realdata/oids_csv', type=str, help='Шлях до CSV з ОІД')
        parser.add_argument('realdata/requests_csv', type=str, help='Шлях до CSV з заявками')
        parser.add_argument('realdata/request_items_csv', type=str, help='Шлях до CSV з елементами заявок')
        parser.add_argument('realdata/documents_csv', type=str, help='Шлях до CSV з документами')

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Починаємо процес імпорту реальних даних...")

        # Імпортуємо в правильному порядку залежностей
        self._import_territorial_managements(options['tu_csv'])
        self._import_units(options['units_csv'])
        self._import_persons(options['persons_csv'])
        self._import_document_types(options['doc_types_csv'])
        self._import_oids(options['oids_csv'])
        self._import_work_requests(options['requests_csv'])
        self._import_work_request_items(options['request_items_csv'])
        self._import_documents(options['documents_csv'])

        self.stdout.write(self.style.SUCCESS("Імпорт реальних даних успішно завершено!"))



    def _import_territorial_managements(self, file_path):
        self.stdout.write(f"Імпорт територіальних управлінь з {file_path}...")
        try:
            with open(file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Використовуємо get_or_create для уникнення дублікатів
                    tu, created = TerritorialManagement.objects.get_or_create(
                        code=row['tu_code'],
                        defaults={'name': row['tu_name']}
                    )
                    if created:
                        self.stdout.write(f"  Створено ТУ: {tu.name}")
                    else:
                        self.stdout.write(f"  ТУ вже існує: {tu.name}")
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Помилка: файл {file_path} не знайдено."))
            raise  # Зупиняємо виконання, якщо файл не знайдено

    def _import_units(self, file_path):
        self.stdout.write(f"Імпорт військових частин з {file_path}...")
        try:
            with open(file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # 1. Знаходимо батьківський об'єкт (TerritorialManagement)
                    try:
                        tu_instance = TerritorialManagement.objects.get(code=row['tu_code'])
                    except TerritorialManagement.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"  Попередження: ТУ з кодом '{row['tu_code']}' не знайдено для ВЧ '{row['unit_code']}'. Пропускаємо."))
                        continue # Переходимо до наступного рядка

                    # 2. Створюємо або оновлюємо об'єкт Unit
                    unit, created = Unit.objects.get_or_create(
                        code=row['unit_code'],
                        defaults={
                            'name': row['full_name'],
                            'city': row['city'],
                            'distance_from_gu': int(row['distance']) if row['distance'] else None,
                            'territorial_management': tu_instance
                        }
                    )
                    if created:
                        self.stdout.write(f"  Створено ВЧ: {unit.code} - {unit.name}")
                    else:
                        self.stdout.write(f"  ВЧ вже існує: {unit.code}")
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Помилка: файл {file_path} не знайдено."))
            raise
        
    def _import_persons(self, file_path):
        self.stdout.write(f"Імпорт виконавців з {file_path}...")
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Person.objects.get_or_create(
                    full_name=row['full_name'],
                    defaults={
                        'position': row['position'],
                        'is_active': row['is_active'].upper() == 'TRUE'
                    }
                )
        self.stdout.write(self.style.SUCCESS('  Виконавців імпортовано.'))

    def _import_document_types(self, file_path):
        self.stdout.write(f"Імпорт типів документів з {file_path}...")
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                DocumentType.objects.get_or_create(
                    name=row['name'],
                    oid_type=row['oid_type'],
                    work_type=row['work_type'],
                    defaults={
                        'has_expiration': row['has_expiration'].upper() == 'TRUE',
                        'duration_months': int(row['duration_months'])
                    }
                )
        self.stdout.write(self.style.SUCCESS('  Типи документів імпортовано.'))

    def _import_oids(self, file_path):
        self.stdout.write(f"Імпорт ОІД з {file_path}...")
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    unit_instance = Unit.objects.get(code=row['unit_code'])
                    OID.objects.get_or_create(
                        cipher=row['cipher'],
                        unit=unit_instance,
                        defaults={
                            'oid_type': row['oid_type'], 
                            'pemin_sub_type': row['pemin_sub_type'], 
                            'serial_number': row['serial_number'], 
                            'full_name': row['full_name'],
							'room': row['room'],
                            'status': row['status'],
                            'sec_level': row['sec_level'],
                            'note': row['note']                           
                        }
                    )
                except Unit.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  Попередження: ВЧ з кодом '{row['unit_code']}' не знайдено для ОІД '{row['cipher']}'. Пропускаємо."))
                    continue
        self.stdout.write(self.style.SUCCESS('  ОІД імпортовано.'))

    def _import_work_requests(self, file_path):
        self.stdout.write(f"Імпорт заявок на роботи з {file_path}...")
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    unit_instance = Unit.objects.get(code=row['unit_code'])
                    WorkRequest.objects.get_or_create(
                        unit=unit_instance,
                        incoming_number=row['incoming_number'],
                        defaults={
                            'incoming_date': datetime.datetime.strptime(row['incoming_date'], '%Y-%m-%d').date(),
                            'status': row['status'],
                            'note': row['note']
                        }
                    )
                except Unit.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  Попередження: ВЧ з кодом '{row['unit_code']}' не знайдено для заявки '{row['incoming_number']}'. Пропускаємо."))
                    continue
        self.stdout.write(self.style.SUCCESS('  Заявки на роботи імпортовано.'))

    def _import_work_request_items(self, file_path):
        self.stdout.write(f"Імпорт елементів заявок з {file_path}...")
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    request_instance = WorkRequest.objects.get(
                        unit__code=row['request_unit_code'],
                        incoming_number=row['request_incoming_number']
                    )
                    oid_instance = OID.objects.get(cipher=row['oid_cipher'])
                    WorkRequestItem.objects.get_or_create(
                        request=request_instance,
                        oid=oid_instance,
                        work_type=row['work_type'],
                        defaults={'status': row['status']}
                    )
                except WorkRequest.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  Попередження: Заявку '{row['request_incoming_number']}' для ВЧ '{row['request_unit_code']}' не знайдено. Пропускаємо елемент."))
                    continue
                except OID.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  Попередження: ОІД з шифром '{row['oid_cipher']}' не знайдено. Пропускаємо елемент."))
                    continue
        self.stdout.write(self.style.SUCCESS('  Елементи заявок імпортовано.'))
        
    def _import_documents(self, file_path):
        self.stdout.write(f"Імпорт документів з {file_path}...")
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    # Шукаємо всі зв'язки
                    oid_instance = OID.objects.get(cipher=row['oid_cipher'])
                    doc_type_instance = DocumentType.objects.get(
                        name=row['document_type_name'],
                        oid_type=row['document_type_oid_type'],
                        work_type=row['document_type_work_type']
                    )
                    author_instance = Person.objects.get(full_name=row['author_full_name'])

                    # Зв'язок з WorkRequestItem є опційним
                    wri_instance = None
                    if row.get('wri_request_number') and row.get('wri_oid_cipher'):
                        try:
                            wri_instance = WorkRequestItem.objects.get(
                                request__incoming_number=row['wri_request_number'],
                                oid__cipher=row['wri_oid_cipher']
                            )
                        except WorkRequestItem.DoesNotExist:
                             self.stdout.write(self.style.WARNING(f"  Попередження: WRI для заявки '{row['wri_request_number']}' та ОІД '{row['wri_oid_cipher']}' не знайдено."))

                    # Створюємо документ
                    Document.objects.get_or_create(
                        document_number=row['document_number'],
                        oid=oid_instance,
                        document_type=doc_type_instance,
                        defaults={
                            'process_date': datetime.datetime.strptime(row['process_date'], '%Y-%m-%d').date(),
                            'work_date': datetime.datetime.strptime(row['work_date'], '%Y-%m-%d').date(),
                            'author': author_instance,
                            'work_request_item': wri_instance,
                            'dsszzi_registered_number': row.get('dsszzi_registered_number') or None,
                            'dsszzi_registered_date': datetime.datetime.strptime(row['dsszzi_registered_date'], '%Y-%m-%d').date() if row.get('dsszzi_registered_date') else None,
                        }
                    )
                except OID.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  Пропуск документа '{row['document_number']}': ОІД '{row['oid_cipher']}' не знайдено."))
                except DocumentType.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  Пропуск документа '{row['document_number']}': Тип документа '{row['document_type_name']}' не знайдено."))
                except Person.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  Пропуск документа '{row['document_number']}': Виконавця '{row['author_full_name']}' не знайдено."))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Невідома помилка при імпорті документа '{row['document_number']}': {e}"))

        self.stdout.write(self.style.SUCCESS('  Документи імпортовано.'))