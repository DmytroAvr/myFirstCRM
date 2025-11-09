# D:\myFirstCRM\oids\management\commands\import_real_data.py

# в файлі oids/management/commands/import_real_data.py

import csv
import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from dateutil import parser as date_parser

# Імпортуємо ваші моделі (замініть на правильні імпорти для вашого проекту)
from oids.models import (
    TerritorialManagement, Unit, Person, DocumentType, OID,
    WorkRequest, WorkRequestItem, Document
)


class Command(BaseCommand):
    help = 'Імпорт даних з CSV файлів'

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str, help='Шляхи до CSV файлів')

    def handle(self, *args, **options):
        files = options['files']
        
        # Порядок імпорту важливий через залежності між моделями
        for file_path in files:
            if 'tu.csv' in file_path:
                self._import_territorial_managements(file_path) 
            elif 'units.csv' in file_path:
                self._import_units(file_path)
            elif 'persons.csv' in file_path:
                self._import_persons(file_path)
            elif 'document_types.csv' in file_path:
                self._import_document_types(file_path)
            elif 'oids.csv' in file_path:
                self._import_oids(file_path)
            elif 'work_requests.csv' in file_path:
                self._import_work_requests(file_path)
            elif 'work_request_items.csv' in file_path:
                self._import_work_request_items(file_path)
            elif 'documents.csv' in file_path:
                self._import_documents(file_path)
    
    def _parse_date(self, date_string):
        """
        Автоматично парсить дату з різних форматів.
        Повертає datetime.date або None якщо не вдалося розпарсити.
        """
        if not date_string or date_string.strip() == '':
            return None
            
        date_string = date_string.strip()
        
        # Список популярних форматів дат для спроби парсингу
        date_formats = [
            '%Y.%m.%d',     # 2024.01.15 (ваш основний формат)
            '%Y-%m-%d',     # 2024-01-15
            '%d.%m.%Y',     # 15.01.2024
            '%d-%m-%Y',     # 15-01-2024
            '%d/%m/%Y',     # 15/01/2024
            '%Y/%m/%d',     # 2024/01/15
            '%m/%d/%Y',     # 01/15/2024 (американський формат)
            '%Y.%m.%d %H:%M:%S',  # з часом
            '%Y-%m-%d %H:%M:%S',  # з часом
        ]
        
        # Спочатку пробуємо стандартні формати
        for fmt in date_formats:
            try:
                parsed_date = datetime.datetime.strptime(date_string, fmt)
                return parsed_date.date()
            except ValueError:
                continue
        
        # Якщо стандартні формати не спрацювали, використовуємо dateutil
        try:
            parsed_date = date_parser.parse(date_string, dayfirst=True)  # dayfirst=True для європейського формату
            return parsed_date.date()
        except (ValueError, TypeError):
            return None


    # --- Функції імпорту ---

    def _import_territorial_managements(self, file_path):
        self.stdout.write(f"Імпорт територіальних управлінь з {file_path}...")
        try:
            with open(file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    TerritorialManagement.objects.get_or_create(
                        code=row['tu_code'], defaults={'name': row['tu_name']}
                    )
            self.stdout.write(self.style.SUCCESS('  Територіальні управління імпортовано.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Помилка: файл '{file_path}' не знайдено. Перевірте шлях."))
            raise

    def _import_units(self, file_path):
        self.stdout.write(f"Імпорт військових частин з {file_path}...")
        try:
            with open(file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        tu_instance = TerritorialManagement.objects.get(code=row['tu_code'])
                        Unit.objects.get_or_create(
                            code=row['unit_code'],
                            defaults={
                                'name': row['full_name'], 'city': row['city'],
                                'distance_from_gu': int(row['distance']) if row['distance'] else 0,
                                'territorial_management': tu_instance
                            }
                        )
                    except TerritorialManagement.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"  Попередження: ТУ з кодом '{row['tu_code']}' не знайдено для ВЧ '{row['unit_code']}'. Пропускаємо."))
                        continue
            self.stdout.write(self.style.SUCCESS('  Військові частини імпортовано.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Помилка: файл '{file_path}' не знайдено."))
            raise
            
    # Додайте решту функцій _import... з попередньої відповіді сюди
    # ... _import_persons, _import_document_types, і т.д. ...
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
                        defaults={ # Змінив на defaults, щоб не оновлювати існуючі ОІД
                            'unit': unit_instance,
                            'oid_type': row['oid_type'], 'full_name': row['full_name'],
                            'room': row['room'], 'status': row['status'],
                            'sec_level': row['sec_level']
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
                            # 'note': row['note']
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
            for i, row in enumerate(reader, start=2): # i - номер рядка для логів
                document_number = row.get('document_number', f'в рядку {i}')
                try:
                    # 1. Шукаємо всі зв'язки
                    oid_instance = OID.objects.get(cipher=row['oid_cipher'])
                    
                    doc_type_instance = DocumentType.objects.get(
                        name=row['document_type_name'],
                        oid_type=row['document_type_oid_type'],
                        work_type=row['document_type_work_type']
                    )
                    
                    author_instance = Person.objects.get(full_name=row['author_full_name'])

                    # 2. Парсимо дати з автоматичним визначенням формату
                    doc_process_date = self._parse_date(row.get('doc_process_date'))
                    work_date = self._parse_date(row.get('work_date'))
                    dsszzi_registered_date = self._parse_date(row.get('dsszzi_registered_date'))
                    
                    # Перевіряємо чи обов'язкові дати були успішно розпарсені
                    if not doc_process_date:
                        raise ValueError(f"Не вдалося розпарсити doc_process_date: '{row.get('doc_process_date')}'")
                    if not work_date:
                        raise ValueError(f"Не вдалося розпарсити work_date: '{row.get('work_date')}'")

                    # 3. Зв'язок з WorkRequestItem є опційним
                    wri_instance = None
                    if row.get('wri_request_number') and row.get('wri_oid_cipher'):
                        try:
                            # Уточнений пошук WRI
                            wri_instance = WorkRequestItem.objects.get(
                                request__incoming_number=row['wri_request_number'],
                                oid__cipher=row['wri_oid_cipher'],
                                # Для надійності можна додати work_type, якщо він є в CSV
                                # work_type=row['wri_work_type'] 
                            )
                        except WorkRequestItem.DoesNotExist:
                             self.stdout.write(self.style.WARNING(f"  Попередження для документа '{document_number}': WRI для заявки '{row.get('wri_request_number')}' та ОІД '{row.get('wri_oid_cipher')}' не знайдено."))
                        except WorkRequestItem.MultipleObjectsReturned:
                             self.stdout.write(self.style.WARNING(f"  Попередження для документа '{document_number}': Знайдено декілька WRI. Зв'язок не встановлено."))

                    # 4. Створюємо або оновлюємо документ
                    doc, created = Document.objects.get_or_create(
                        document_number=document_number,
                        defaults={
                            'oid': oid_instance,
                            'document_type': doc_type_instance,
                            'doc_process_date': doc_process_date,
                            'work_date': work_date,
                            'author': author_instance,
                            'work_request_item': wri_instance,
                            'dsszzi_registered_number': row.get('dsszzi_registered_number') or None,
                            'dsszzi_registered_date': dsszzi_registered_date,
                        }
                    )
                    if not created:
                        self.stdout.write(f"  Документ '{document_number}' вже існує. Дані не оновлено.")
                    else:
                        self.stdout.write(f"  Успішно імпортовано документ '{document_number}'")

                # --- Блок обробки помилок для одного рядка ---
                except OID.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"  ПОМИЛКА в рядку {i}: Не вдалося імпортувати документ '{document_number}'. Причина: ОІД з шифром '{row.get('oid_cipher')}' не знайдено."))
                except DocumentType.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"  ПОМИЛКА в рядку {i}: Не вдалося імпортувати документ '{document_number}'. Причина: Тип документа з параметрами (name='{row.get('document_type_name')}', oid_type='{row.get('document_type_oid_type')}', work_type='{row.get('document_type_work_type')}') не знайдено в базі."))
                except Person.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"  ПОМИЛКА в рядку {i}: Не вдалося імпортувати документ '{document_number}'. Причина: Виконавець з ім'ям '{row.get('author_full_name')}' не знайдений."))
                except ValueError as e:
                    self.stdout.write(self.style.ERROR(f"  ПОМИЛКА в рядку {i}: Не вдалося імпортувати документ '{document_number}'. Причина: {e}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  НЕВІДОМА ПОМИЛКА в рядку {i} для документа '{document_number}': {e}"))
        
        self.stdout.write(self.style.SUCCESS('  Імпорт документів завершено.'))
        
	