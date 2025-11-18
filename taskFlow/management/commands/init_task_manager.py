"""
Management команди для Task Manager
Розмістити: taskFlow/management/commands/init_task_manager.py
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from taskFlow.models import Person, Project, Status, Task, PersonGroup


class Command(BaseCommand):
    help = 'Ініціалізація Task Manager з демо-даними'

    def add_arguments(self, parser):
        parser.add_argument(
            '--demo',
            action='store_true',
            help='Створити демо-дані (проєкти, користувачі, завдання)',
        )
        parser.add_argument(
            '--statuses',
            action='store_true',
            help='Створити тільки глобальні статуси',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options['statuses'] or not options['demo']:
            self.create_global_statuses()
        
        if options['demo']:
            self.create_demo_data()

    def create_global_statuses(self):
        """Створення глобальних статусів"""
        self.stdout.write('Створення глобальних статусів...')
        
        statuses = [
            {
                'name': 'Беклог',
                'color': 'bg-gray-500',
                'order': 1,
                'is_default': True,
                'is_final': False,
            },
            {
                'name': 'До виконання',
                'color': 'bg-blue-500',
                'order': 2,
                'is_default': False,
                'is_final': False,
            },
            {
                'name': 'В роботі',
                'color': 'bg-yellow-500',
                'order': 3,
                'is_default': False,
                'is_final': False,
            },
            {
                'name': 'На перевірці',
                'color': 'bg-purple-500',
                'order': 4,
                'is_default': False,
                'is_final': False,
            },
            {
                'name': 'Виконано',
                'color': 'bg-green-500',
                'order': 5,
                'is_default': False,
                'is_final': True,
            },
            {
                'name': 'Заблоковано',
                'color': 'bg-red-500',
                'order': 6,
                'is_default': False,
                'is_final': False,
            },
        ]
        
        created_count = 0
        for status_data in statuses:
            status, created = Status.objects.get_or_create(
                name=status_data['name'],
                project=None,
                defaults=status_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Створено статус: {status.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Створено {created_count} нових статусів')
        )

    def create_demo_data(self):
        """Створення демо-даних"""
        self.stdout.write('Створення демо-даних...')
        
        # 1. Створення виконавців
        self.stdout.write('\n1. Створення виконавців...')
        persons_data = [
            {
                'full_name': 'Іваненко Іван',
                'surname': 'Іваненко',
                'position': 'Керівник проєкту',
                'group': PersonGroup.GOV,
            },
            {
                'full_name': 'Петренко Петро',
                'surname': 'Петренко',
                'position': 'Розробник',
                'group': PersonGroup.IARM,
            },
            {
                'full_name': 'Сидоренко Сидір',
                'surname': 'Сидоренко',
                'position': 'Аналітик',
                'group': PersonGroup.ZBSI,
            },
            {
                'full_name': 'Коваленко Катерина',
                'surname': 'Коваленко',
                'position': 'Тестувальник',
                'group': PersonGroup.SDKTK,
            },
            {
                'full_name': 'Мельник Марія',
                'surname': 'Мельник',
                'position': 'Дизайнер',
                'group': PersonGroup.GOV,
            },
        ]
        
        persons = {}
        for person_data in persons_data:
            person, created = Person.objects.get_or_create(
                full_name=person_data['full_name'],
                defaults=person_data
            )
            persons[person_data['surname']] = person
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Створено: {person.full_name}')
                )
        
        # 2. Створення проєктів
        self.stdout.write('\n2. Створення проєктів...')
        projects_data = [
            {
                'name': 'Розробка веб-порталу',
                'key': 'WEB',
                'description': 'Створення корпоративного веб-порталу',
                'group': PersonGroup.IARM,
                'use_custom_statuses': False,
            },
            {
                'name': 'Модернізація інфраструктури',
                'key': 'INFRA',
                'description': 'Оновлення серверного обладнання',
                'group': PersonGroup.ZBSI,
                'use_custom_statuses': True,
            },
            {
                'name': 'Впровадження CRM',
                'key': 'CRM',
                'description': 'Впровадження системи управління клієнтами',
                'group': PersonGroup.GOV,
                'use_custom_statuses': False,
            },
        ]
        
        projects = {}
        for project_data in projects_data:
            project, created = Project.objects.get_or_create(
                key=project_data['key'],
                defaults=project_data
            )
            projects[project_data['key']] = project
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Створено: {project.name} ({project.key})')
                )
        
        # 3. Створення завдань
        self.stdout.write('\n3. Створення завдань...')
        
        # Отримуємо дефолтний статус
        default_status = Status.objects.filter(
            project=None,
            is_default=True
        ).first()
        
        in_progress_status = Status.objects.filter(
            project=None,
            name='В роботі'
        ).first()
        
        done_status = Status.objects.filter(
            project=None,
            is_final=True
        ).first()
        
        from datetime import date, timedelta
        
        tasks_data = [
            # Завдання для WEB проєкту
            {
                'project': projects['WEB'],
                'title': 'Розробка дизайну головної сторінки',
                'description': 'Створити макет головної сторінки порталу',
                'assignee': persons['Мельник'],
                'department': PersonGroup.GOV,
                'priority': 'high',
                'status': in_progress_status,
                'due_date': date.today() + timedelta(days=7),
                'created_by': persons['Іваненко'],
            },
            {
                'project': projects['WEB'],
                'title': 'Налаштування бази даних',
                'description': 'Створити структуру БД для порталу',
                'assignee': persons['Петренко'],
                'department': PersonGroup.IARM,
                'priority': 'critical',
                'status': default_status,
                'due_date': date.today() + timedelta(days=3),
                'created_by': persons['Іваненко'],
            },
            {
                'project': projects['WEB'],
                'title': 'Розробка API',
                'description': 'Реалізувати REST API для порталу',
                'assignee': persons['Петренко'],
                'department': PersonGroup.IARM,
                'priority': 'high',
                'status': default_status,
                'due_date': date.today() + timedelta(days=14),
                'created_by': persons['Іваненко'],
            },
            
            # Завдання для INFRA проєкту
            {
                'project': projects['INFRA'],
                'title': 'Аудит поточної інфраструктури',
                'description': 'Провести повний аудит серверного обладнання',
                'assignee': persons['Сидоренко'],
                'department': PersonGroup.ZBSI,
                'priority': 'medium',
                'status': done_status,
                'due_date': date.today() - timedelta(days=5),
                'created_by': persons['Іваненко'],
                'is_completed': True,
            },
            {
                'project': projects['INFRA'],
                'title': 'Закупівля нового обладнання',
                'description': 'Оформити замовлення на нові сервери',
                'assignee': persons['Іваненко'],
                'department': PersonGroup.GOV,
                'priority': 'high',
                'status': in_progress_status,
                'due_date': date.today() + timedelta(days=10),
                'created_by': persons['Іваненко'],
            },
            
            # Завдання для CRM проєкту
            {
                'project': projects['CRM'],
                'title': 'Вибір CRM системи',
                'description': 'Дослідити ринок та обрати оптимальну CRM',
                'assignee': persons['Сидоренко'],
                'department': PersonGroup.ZBSI,
                'priority': 'high',
                'status': in_progress_status,
                'due_date': date.today() + timedelta(days=5),
                'created_by': persons['Іваненко'],
            },
            {
                'project': projects['CRM'],
                'title': 'Підготовка технічного завдання',
                'description': 'Скласти ТЗ для впровадження CRM',
                'assignee': persons['Коваленко'],
                'department': PersonGroup.SDKTK,
                'priority': 'medium',
                'status': default_status,
                'due_date': date.today() + timedelta(days=20),
                'created_by': persons['Іваненко'],
            },
        ]
        
        created_count = 0
        for task_data in tasks_data:
            # Перевіряємо чи завдання вже існує
            existing = Task.objects.filter(
                project=task_data['project'],
                title=task_data['title']
            ).first()
            
            if not existing:
                task = Task.objects.create(**task_data)
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Створено: {task.key} - {task.title}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Створено {created_count} нових завдань')
        )
        
        # Підсумок
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Демо-дані успішно створено!'))
        self.stdout.write('='*60)
        self.stdout.write(f'Виконавців: {Person.objects.count()}')
        self.stdout.write(f'Проєктів: {Project.objects.count()}')
        self.stdout.write(f'Статусів: {Status.objects.count()}')
        self.stdout.write(f'Завдань: {Task.objects.count()}')
        self.stdout.write('='*60)