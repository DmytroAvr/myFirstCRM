# oids/management/commands/import_real_data.py

import csv
import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from dateutil import parser as date_parser

# Імпортуємо всі необхідні моделі
from oids.models import (
    TerritorialManagement, Unit, Person, DocumentType, OID, DskEot,
    WorkRequest, WorkRequestItem, Document, Declaration,
    Trip, TechnicalTask, DeclarationRegistration
)

class Command(BaseCommand):
    help = 'Імпорт даних з CSV файлів у правильному порядку'

    def add_arguments(self, parser):
        parser.add_argument('files', nargs='+', type=str, help='Шляхи до CSV файлів')

    @transaction.atomic
    def handle(self, *args, **options):
        files = options['files']
        
        # Визначаємо порядок імпорту, щоб уникнути помилок залежностей
        import_order = [
            ('tu.csv', self._import_territorial_managements),
            ('units.csv', self._import_units),
            ('persons.csv', self._import_persons),
            ('document_types.csv', self._import_document_types),
            ('oids.csv', self._import_oids),
            ('dsk_eot.csv', self._import_dsk_eot), # <-- Нова модель
            ('work_requests.csv', self._import_work_requests),
            ('work_request_items.csv', self._import_work_request_items),
            ('technical_tasks.csv', self._import_technical_tasks), # <-- Нова функція
            ('documents.csv', self._import_documents),
            ('declarations.csv', self._import_declarations), # <-- Нова модель
            ('trips.csv', self._import_trips), # <-- Нова функція
            # Додайте сюди файли для DeclarationRegistration, якщо потрібно
        ]

        for file_pattern, import_func in import_order:
            for file_path in files:
                if file_pattern in file_path:
                    import_func(file_path)
                    break # Переходимо до наступного типу файлу

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
                return parsed_date.strftime('%Y-%m-%d')
                # return parsed_date.date()
            except ValueError:
                continue
        
        # Якщо стандартні формати не спрацювали, використовуємо dateutil
        try:
            parsed_date = date_parser.parse(date_string, dayfirst=True)  # dayfirst=True для європейського формату
            return parsed_date.strftime('%Y-%m-%d')
            # return parsed_date.date()
        except (ValueError, TypeError):
            return None

    # --- ІСНУЮЧІ ФУНКЦІЇ ІМПОРТУ (залишаються без змін) ---

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
            
    def _import_persons(self, file_path):
        self.stdout.write(f"Імпорт виконавців з {file_path}...")
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Person.objects.get_or_create(
                    full_name=row['full_name'],
                    defaults={
                        'position': row['position'],
                        'group': row['group'],
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

    # def _import_oids(self, file_path):
    #     self.stdout.write(f"Імпорт ОІД з {file_path}...")
    #     with open(file_path, mode='r', encoding='utf-8') as csvfile:
    #         reader = csv.DictReader(csvfile)
    #         for row in reader:
    #             try:
    #                 unit_instance = Unit.objects.get(code=row['unit_code'])
    #                 OID.objects.get_or_create(
    #                     cipher=row['cipher'],
    #                     defaults={ # Змінив на defaults, щоб не оновлювати існуючі ОІД
    #                         'unit': unit_instance,
    #                         'oid_type': row['oid_type'], 'full_name': row['full_name'],
    #                         'room': row['room'], 'status': row['status'],
    #                         'sec_level': row['sec_level']
    #                     }
    #                 )
    #             except Unit.DoesNotExist:
    #                 self.stdout.write(self.style.WARNING(f"  Попередження: ВЧ з кодом '{row['unit_code']}' не знайдено для ОІД '{row['cipher']}'. Пропускаємо."))
    #                 continue
    #     self.stdout.write(self.style.SUCCESS('  ОІД імпортовано.'))

    def _import_oids(self, file_path):
        self.stdout.write(f"Імпорт ОІД з {file_path}...")
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    unit_instance = Unit.objects.get(code=row['unit_code'])
                    
                    # Створюємо або знаходимо ОІД за його унікальним шифром
                    oid_instance, created = OID.objects.get_or_create(
                        cipher=row['cipher'],
                        # Ми шукаємо за шифром, тому він має бути унікальним.
                        # Якщо шифри не унікальні, потрібно додати unit до пошуку:
                        # unit=unit_instance,
                        defaults={
                            'unit': unit_instance,
                            'oid_type': row['oid_type'],
                            'full_name': row['full_name'],
                            'room': row['room'],
                            'status': row['status'],
                            'sec_level': row.get('sec_level', 'Таємно'), # Значення за замовчуванням, якщо поле відсутнє
                            
                            # --- НОВІ ПОЛЯ ---
                            # Використовуємо .get() для необов'язкових полів.
                            # Якщо в CSV немає стовпця, .get() поверне None, і поле в базі буде NULL.
                            'pemin_sub_type': row.get('pemin_sub_type') or None,
                            'serial_number': row.get('serial_number') or None,
                            'inventory_number': row.get('inventory_number') or None,
                            'note': row.get('note') or None,
                        }
                    )
                    
                    if created:
                        self.stdout.write(f"  Створено ОІД: {oid_instance.cipher}")
                    else:
                        self.stdout.write(f"  ОІД {oid_instance.cipher} вже існує, не оновлювався.")

                except Unit.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  Попередження: ВЧ з кодом '{row['unit_code']}' не знайдено для ОІД '{row['cipher']}'. Пропускаємо."))
                    continue
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  Помилка при обробці ОІД '{row.get('cipher', 'N/A')}': {e}"))
                    
        self.stdout.write(self.style.SUCCESS('  Імпорт ОІД завершено.'))
        
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
            for i, row in enumerate(reader, start=2):
                document_number = row.get('document_number', f'в рядку {i}')
                try:
                    # --- 1. НАДІЙНИЙ ПОШУК ОІДа ЗА КОМБІНАЦІЄЮ ВЧ + ШИФР ---
                    # Переконуємося, що в CSV є стовпці 'unit_code' та 'oid_cipher'
                    unit_code = row['unit_code']
                    oid_cipher = row['oid_cipher']
                    
                    oid_instance = OID.objects.get(
                        unit__code=unit_code,
                        cipher=oid_cipher
                    )
                    
                    # --- Решта логіки пошуку залишається без змін ---
                    doc_type_instance = DocumentType.objects.get(
                        name=row['document_type_name'],
                        oid_type=row['document_type_oid_type'],
                        work_type=row['document_type_work_type']
                    )
                    author_instance = Person.objects.get(full_name=row['author_full_name'])

                    # --- 2. Парсинг дат (без змін) ---
                    doc_process_date = self._parse_date(row.get('doc_process_date'))
                    work_date = self._parse_date(row.get('work_date'))
                    dsszzi_registered_date = self._parse_date(row.get('dsszzi_registered_date'))
                    
                    if not doc_process_date or not work_date:
                        raise ValueError(f"Обов'язкові дати (doc_process_date, work_date) не можуть бути порожніми.")

                    # --- 3. Зв'язок з WorkRequestItem (без змін) ---
                    wri_instance = None
                    if row.get('wri_request_number') and row.get('wri_oid_cipher'):
                        try:
                            # Шукаємо WRI, використовуючи вже точно знайдений ОІД
                            wri_instance = WorkRequestItem.objects.get(
                                request__incoming_number=row['wri_request_number'],
                                oid=oid_instance 
                            )
                        except WorkRequestItem.DoesNotExist:
                            self.stdout.write(self.style.WARNING(f"  Попередження: WRI для заявки '{row.get('wri_request_number')}' та ОІД '{row.get('wri_oid_cipher')}' не знайдено."))
                        except WorkRequestItem.MultipleObjectsReturned:
                            self.stdout.write(self.style.WARNING(f"  Попередження: Знайдено декілька WRI для документа '{document_number}'. Зв'язок не встановлено."))
                    
                   # 4. Створюємо АБО ОНОВЛЮЄМО документ
                    # Використовуємо update_or_create для гарантованого оновлення
                    doc, created = Document.objects.update_or_create(
                        document_number=document_number,
                        oid=oid_instance,
                        defaults={
                            'document_type': doc_type_instance,
                            'doc_process_date': doc_process_date,
                            'work_date': work_date,
                            'author': author_instance,
                            'work_request_item': wri_instance,
                            'dsszzi_registered_number': row.get('dsszzi_registered_number') or None,
                            'dsszzi_registered_date': dsszzi_registered_date,
                            'expiration_date': None
                        }
                    )
                    print(f"DEBUG: self.document_type {doc_type_instance}  ")
                    print(f"DEBUG: self.document_type {row.get('document_type_name')}  ")
                    print(f"DEBUG: self.document_type {row.get('document_type_oid_type')}  ")
                    print(f"DEBUG: self.document_type {row.get('document_type_work_type')}  ")
                    print(f"DEBUG: self.document_type {row.get('doc_process_date')}  ")
                    print(f"DEBUG: self.document_type {row.get('work_date')}  ")
                    print(f"DEBUG: self.document_type {row.get('author')}  ")
                    print(f"DEBUG: self.document_type {row.get('work_request_item')}  ")
                    print(f"DEBUG: self.document_type {row.get('dsszzi_registered_number')}  ")
                    print(f"DEBUG: self.document_type {row.get('dsszzi_registered_date')}  ")

                    if not created:
                        self.stdout.write(f"  Документ '{document_number}' для ОІД '{oid_cipher}' вже існує.")
                    else:
                        self.stdout.write(f"  Успішно імпортовано документ '{document_number}'")

                # --- Блок обробки помилок ---
                except OID.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"  ПОМИЛКА в рядку {i}: Не вдалося імпортувати документ '{document_number}'. Причина: ОІД з шифром '{row.get('oid_cipher')}' для ВЧ '{row.get('unit_code')}' не знайдено."))
                except KeyError as e:
                    self.stdout.write(self.style.ERROR(f"  ПОМИЛКА в рядку {i}: У CSV-файлі відсутній необхідний стовпець: {e}."))
                except DocumentType.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"  ПОМИЛКА в рядку {i}: Не вдалося імпортувати документ '{document_number}'. Причина: Тип документа з параметрами (name='{row.get('document_type_name')}', oid_type='{row.get('document_type_oid_type')}', work_type='{row.get('document_type_work_type')}') не знайдено в базі."))
                except Person.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"  ПОМИЛКА в рядку {i}: Не вдалося імпортувати документ '{document_number}'. Причина: Виконавець з ім'ям '{row.get('author_full_name')}' не знайдений."))
                except ValueError as e:
                    self.stdout.write(self.style.ERROR(f"  ПОМИЛКА в рядку {i}: Не вдалося імпортувати документ '{document_number}'. Причина: {e}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  НЕВІДОМА ПОМИЛКА в рядку {i} для документа '{document_number}': {e}"))
        
        self.stdout.write(self.style.SUCCESS('  Імпорт документів завершено.'))
  
    # --- НОВІ ФУНКЦІЇ ІМПОРТУ ---

    def _import_dsk_eot(self, file_path):
        self.stdout.write(f"Імпорт об'єктів ДСК ЕОТ з {file_path}...")
        try:
            with open(file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        unit_instance = Unit.objects.get(code=row['unit_code'])
                        DskEot.objects.get_or_create(
                            cipher=row['cipher'],
                            unit=unit_instance,
                            defaults={
                                'serial_number': row.get('serial_number'),
                                'inventory_number': row.get('inventory_number'),
                                'room': row.get('room'),
                                'security_level': row.get('security_level', 'ДСК'),
                            }
                        )
                    except Unit.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"  Попередження: ВЧ з кодом '{row['unit_code']}' не знайдено для ДСК ЕОТ '{row['cipher']}'. Пропускаємо."))
                        continue
            self.stdout.write(self.style.SUCCESS('  Об\'єкти ДСК ЕОТ імпортовано.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Помилка: файл '{file_path}' не знайдено."))

    def _import_declarations(self, file_path):
        self.stdout.write(f"Імпорт Декларацій відповідності з {file_path}...")
        try:
            with open(file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        dsk_eot_instance = DskEot.objects.get(cipher=row['dsk_eot_cipher'])
                        Declaration.objects.get_or_create(
                            prepared_number=row['prepared_number'],
                            dsk_eot=dsk_eot_instance,
                            defaults={
                                'prepared_date': self._parse_date(row['prepared_date']),
                                'registered_number': row.get('registered_number'),
                                'registered_date': self._parse_date(row.get('registered_date')),
                            }
                        )
                    except DskEot.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"  Попередження: ДСК ЕОТ з шифром '{row['dsk_eot_cipher']}' не знайдено. Пропускаємо декларацію '{row['prepared_number']}'."))
                        continue
            self.stdout.write(self.style.SUCCESS('  Декларації відповідності імпортовано.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Помилка: файл '{file_path}' не знайдено."))

    def _import_technical_tasks(self, file_path):
        self.stdout.write(f"Імпорт Технічних Завдань з {file_path}...")
        try:
            with open(file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        oid_instance = OID.objects.get(cipher=row['oid_cipher'])
                        reviewed_by_instance = Person.objects.get(full_name=row['reviewed_by_full_name']) if row.get('reviewed_by_full_name') else None
                        
                        TechnicalTask.objects.get_or_create(
                            oid=oid_instance,
                            input_number=row['input_number'],
                            defaults={
                                'input_date': self._parse_date(row['input_date']),
                                'read_till_date': self._parse_date(row['read_till_date']),
                                'review_result': row['review_result'],
                                'reviewed_by': reviewed_by_instance
                            }
                        )
                    except OID.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"  Попередження: ОІД '{row['oid_cipher']}' не знайдено для ТЗ '{row['input_number']}'. Пропускаємо."))
                    except Person.DoesNotExist:
                         self.stdout.write(self.style.WARNING(f"  Попередження: Виконавця '{row['reviewed_by_full_name']}' не знайдено для ТЗ '{row['input_number']}'. Пропускаємо."))
            self.stdout.write(self.style.SUCCESS('  Технічні Завдання імпортовано.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Помилка: файл '{file_path}' не знайдено."))

    def _import_trips(self, file_path):
        self.stdout.write(f"Імпорт Відряджень з {file_path}...")
        try:
            with open(file_path, mode='r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    try:
                        # Створюємо або знаходимо відрядження за унікальним полем, наприклад, purpose
                        trip_instance, created = Trip.objects.get_or_create(
                            purpose=row['purpose'],
                            start_date=self._parse_date(row['start_date']),
                            end_date=self._parse_date(row['end_date']),
                        )
                        if created:
                            # Додаємо M2M зв'язки, якщо це новий запис
                            unit_codes = [code.strip() for code in row.get('unit_codes', '').split(',') if code.strip()]
                            oid_ciphers = [cipher.strip() for cipher in row.get('oid_ciphers', '').split(',') if cipher.strip()]
                            person_names = [name.strip() for name in row.get('person_names', '').split(',') if name.strip()]
                            wr_numbers = [num.strip() for num in row.get('wr_numbers', '').split(',') if num.strip()]

                            trip_instance.units.set(Unit.objects.filter(code__in=unit_codes))
                            trip_instance.oids.set(OID.objects.filter(cipher__in=oid_ciphers))
                            trip_instance.persons.set(Person.objects.filter(full_name__in=person_names))
                            trip_instance.work_requests.set(WorkRequest.objects.filter(incoming_number__in=wr_numbers))
                            
                            self.stdout.write(f"  Створено відрядження: '{trip_instance.purpose[:50]}...'")
                        else:
                            self.stdout.write(f"  Відрядження '{trip_instance.purpose[:50]}...' вже існує.")
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"  Помилка при обробці рядка для відрядження '{row.get('purpose')}': {e}"))
            self.stdout.write(self.style.SUCCESS('  Відрядження імпортовано.'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"Помилка: файл '{file_path}' не знайдено."))