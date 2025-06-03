# oids/management/commands/import_units_from_csv.py
import csv
from django.core.management.base import BaseCommand
from oids.models import Unit, TerritorialManagement # Ваші моделі

class Command(BaseCommand):
    help = 'Imports units from a specified CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file_path', type=str, help='The CSV file path')

    def handle(self, *args, **options):
        file_path = options['csv_file_path']
        self.stdout.write(f"Starting import from {file_path}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Припускаємо, що CSV має колонки 'code', 'name', 'city', 'tm_code'
                    tm_code = row.get('tm_code')
                    tm = None
                    if tm_code:
                        tm, _ = TerritorialManagement.objects.get_or_create(code=tm_code, defaults={'name': f"ТУ {tm_code}"})

                    unit, created = Unit.objects.get_or_create(
                        code=row['code'],
                        defaults={
                            'name': row.get('name'),
                            'city': row.get('city'),
                            'territorial_management': tm
                            # ... інші поля ...
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(f"Successfully created Unit {unit.code}"))
                    else:
                        self.stdout.write(f"Unit {unit.code} already exists.")
        except FileNotFoundError:
            self.stderr.write(self.style.ERROR(f"File not found: {file_path}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"An error occurred: {e}"))
        self.stdout.write("Import finished.")
        
# . Створення кастомних Django Management Commands:
# Коли використовувати: Для імпорту даних з зовнішніх файлів (CSV, Excel, JSON, XML), для разового масового заповнення, або для періодичних завдань імпорту.
# Як це працює: Ви створюєте Python-скрипт у спеціальній директорії вашого додатку (your_app/management/commands/your_command_name.py). Цей скрипт успадковує BaseCommand з django.core.management.base і реалізує метод handle(), в якому ви пишете логіку для читання даних та створення об'єктів моделей Django.
# Приклад структури:
# Запуск команди: python manage.py import_units_from_csv /шлях/до/вашого/файлу.csv
# Переваги: Потужний, гнучкий, можна автоматизувати, добре підходить для великих обсягів та складних перетворень даних.
# Недоліки: Потребує програмування.