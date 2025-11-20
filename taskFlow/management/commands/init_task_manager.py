"""
Management команди для Task Manager
Розмістити: taskFlow/management/commands/init_task_manager.py
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from oids.models import Person, PersonGroup  # Імпорт з oids
from taskFlow.models import Project, Status, Task

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
            # {
            #     'full_name': 'Іваненко Іван',
            #     'surname': 'Іваненко',
            #     'position': 'Керівник проєкту',
            #     'group': PersonGroup.GOV,
            # },
            {
                'full_name': 'Петренко Петро',
                'surname': 'Петренко',
                'position': 'Розробник',
                'group': PersonGroup.IARM,
                'username': 'petrenko',
                'email': '',
                'password': 'demo123',
            },
        ]
        
        persons = {}
        for person_data in persons_data:
            # Витягуємо дані для User
            username = person_data.pop('username')
            email = person_data.pop('email')
            password = person_data.pop('password')
            
            # Створюємо або отримуємо User
            user, user_created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': person_data.get('full_name', '').split()[1] if len(person_data.get('full_name', '').split()) > 1 else '',
                    'last_name': person_data.get('surname', ''),
                }
            )
            
            # Встановлюємо пароль якщо користувач щойно створений
            if user_created:
                user.set_password(password)
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Створено User: {username} (пароль: {password})')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠ User вже існує: {username}')
                )
            
            # Створюємо або отримуємо Person
            person, person_created = Person.objects.get_or_create(
                full_name=person_data['full_name'],
                defaults=person_data
            )
            
            # Прив'язуємо User до Person
            if not person.user:
                person.user = user
                person.save()
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Створено Person: {person.full_name} → {username}')
                )
            elif person.user != user:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ Person {person.full_name} вже прив\'язаний до {person.user.username}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Person існує: {person.full_name} → {username}')
                )
            
            persons[person_data['surname']] = person
        
        
        # 2. Створення проєктів
        self.stdout.write('\n2. Створення проєктів...')
        projects_data = [
            {
                'name': 'Загальна',
                'key': 'ZAG',
                'description': 'Загальні завдання',
                'group': PersonGroup.ZAG,
                'use_custom_statuses': False,
            },
            {
                'name': 'Управління',
                'key': 'GOV',
                'description': 'Управління',
                'group': PersonGroup.GOV,
                'use_custom_statuses': False,
            },
            {
                'name': 'ЗБСІ',
                'key': 'ZBSI',
                'description': 'ЗБСІ',
                'group': PersonGroup.ZBSI,
                'use_custom_statuses': True,
            },
			{
                'name': 'ІАРМ',
                'key': 'IARM',
                'description': 'ІАРМ',
                'group': PersonGroup.IARM,
                'use_custom_statuses': True,
            },
			{
                'name': 'СД КТК',
                'key': 'SDKTK',
                'description': 'СД КТК',
                'group': PersonGroup.SDKTK,
                'use_custom_statuses': True,
            },
            {
                'name': 'Майстерня',
                'key': 'REPAIR',
                'description': 'Майстерня',
                'group': PersonGroup.REPAIR,
                'use_custom_statuses': False,
            },
            {
                'name': 'ПДТР',
                'key': 'PDTR',
                'description': 'ПДТР',
                'group': PersonGroup.PDTR,
                'use_custom_statuses': False,
            },
            {
                'name': 'Аудит З ТЗІ',
                'key': 'AUD',
                'description': 'Аудит З ТЗІ',
                'group': PersonGroup.AUD,
                'use_custom_statuses': False,
            },
            {
                'name': 'Служба ТЗІ',
                'key': 'SL',
                'description': 'Служба ТЗІ',
                'group': PersonGroup.SL,
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
            # {
            #     'project': projects['WEB'],
            #     'title': 'Розробка дизайну головної сторінки',
            #     'description': 'Створити макет головної сторінки порталу',
            #     'assignee': persons['Мельник'],
            #     'department': PersonGroup.GOV,
            #     'priority': 'high',
            #     'status': in_progress_status,
            #     'due_date': date.today() + timedelta(days=7),
            #     'created_by': persons['Іваненко'],
            # },

            
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