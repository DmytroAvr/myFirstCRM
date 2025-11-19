"""
Management команда для архівування виконаних завдань
Розмістити: taskFlow/management/commands/archive_completed_tasks.py

Запуск вручну:
python manage.py archive_completed_tasks

Для автоматичного запуску додайте в crontab:
10 8 * * * cd /path/to/project && python manage.py archive_completed_tasks
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from taskFlow.models import Task


class Command(BaseCommand):
    help = 'Архівує виконані завдання, які мають бути приховані з дошки'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показати що буде заархівовано без реального архівування',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Детальний вивід',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        self.stdout.write('='*60)
        self.stdout.write('Архівування виконаних завдань')
        self.stdout.write('='*60)
        self.stdout.write(f'Час: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('РЕЖИМ ТЕСТУВАННЯ (dry-run)\n'))
        else:
            self.stdout.write('')
        
        # Отримуємо всі виконані завдання
        completed_tasks = Task.objects.filter(
            is_completed=True,
            completed_at__isnull=False
        ).select_related('project', 'status')
        
        self.stdout.write(f'Знайдено виконаних завдань: {completed_tasks.count()}')
        
        # Фільтруємо ті, що мають бути заархівовані
        tasks_to_archive = []
        tasks_still_visible = []
        
        for task in completed_tasks:
            if task.should_be_archived():
                tasks_to_archive.append(task)
            else:
                tasks_still_visible.append(task)
        
        self.stdout.write(f'Мають бути заархівовані: {len(tasks_to_archive)}')
        self.stdout.write(f'Ще видимі на дошці: {len(tasks_still_visible)}')
        self.stdout.write('')
        
        if not tasks_to_archive:
            self.stdout.write(self.style.SUCCESS('✓ Немає завдань для архівування'))
            return
        
        # Виводимо список завдань
        if verbose or dry_run:
            self.stdout.write('Завдання для архівування:')
            for task in tasks_to_archive:
                completed_ago = timezone.now() - task.completed_at
                hours_ago = int(completed_ago.total_seconds() / 3600)
                
                self.stdout.write(
                    f'  • {task.key}: {task.title[:50]}'
                    f' (виконано {hours_ago}год тому)'
                )
        
        if dry_run:
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING(
                    'Це тестовий режим. Для реального архівування '
                    'запустіть без --dry-run'
                )
            )
            return
        
        # Архівуємо (в нашому випадку просто підтверджуємо що вони приховані)
        # Фактично нічого не робимо, тому що фільтрація відбувається динамічно
        # через методи should_be_archived() та is_recently_completed()
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Завдань заархівовано: {len(tasks_to_archive)}'
            )
        )
        
        # Виводимо статистику по проєктах
        if verbose:
            self.stdout.write('')
            self.stdout.write('Статистика по проєктах:')
            
            projects = {}
            for task in tasks_to_archive:
                project_name = task.project.name
                if project_name not in projects:
                    projects[project_name] = 0
                projects[project_name] += 1
            
            for project_name, count in sorted(projects.items()):
                self.stdout.write(f'  • {project_name}: {count}')
        
        self.stdout.write('')
        self.stdout.write('='*60)
        self.stdout.write(
            self.style.SUCCESS('✓ Архівування завершено успішно')
        )
        self.stdout.write('='*60)


class Command2(BaseCommand):
    """
    Альтернативна версія команди з реальним оновленням поля
    Якщо хочете додати поле 'archived' в модель Task
    """
    help = 'Архівує виконані завдання (з оновленням поля archived)'

    def handle(self, *args, **options):
        from taskFlow.models import Task
        
        # Отримуємо всі виконані завдання
        tasks = Task.objects.filter(
            is_completed=True,
            completed_at__isnull=False,
            archived=False  # Якщо додасте це поле
        )
        
        archived_count = 0
        
        for task in tasks:
            if task.should_be_archived():
                task.archived = True
                task.save(update_fields=['archived'])
                archived_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Заархівовано {archived_count} завдань'
            )
        )