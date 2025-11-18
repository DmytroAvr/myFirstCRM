"""
Django Signals для Task Manager
Автоматична обробка подій та ведення історії
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Task, TaskHistory, TaskComment, Status, Project


@receiver(pre_save, sender=Task)
def track_task_changes(sender, instance, **kwargs):
    """
    Відстеження змін завдання перед збереженням
    Створює записи в історії для важливих полів
    """
    if not instance.pk:
        # Нове завдання - не відстежуємо
        return
    
    try:
        old_instance = Task.objects.get(pk=instance.pk)
    except Task.DoesNotExist:
        return
    
    # Поля для відстеження
    fields_to_track = {
        'status': 'Статус',
        'assignee': 'Виконавець',
        'priority': 'Пріоритет',
        'due_date': 'Термін виконання',
        'department': 'Підрозділ',
    }
    
    changes = []
    
    for field, field_label in fields_to_track.items():
        old_value = getattr(old_instance, field)
        new_value = getattr(instance, field)
        
        if old_value != new_value:
            # Форматуємо значення для історії
            old_display = _format_field_value(field, old_value)
            new_display = _format_field_value(field, new_value)
            
            changes.append({
                'field_name': field_label,
                'old_value': old_display,
                'new_value': new_display,
            })
    
    # Зберігаємо зміни в атрибуті екземпляра для post_save
    instance._changes_to_log = changes


@receiver(post_save, sender=Task)
def log_task_changes(sender, instance, created, **kwargs):
    """
    Логування змін завдання після збереження
    """
    if created:
        # Системний коментар про створення завдання
        TaskComment.objects.create(
            task=instance,
            author=instance.created_by,
            text=f"Завдання створено",
            is_system=True
        )
        return
    
    # Логуємо зміни, які були відстежені в pre_save
    if hasattr(instance, '_changes_to_log'):
        for change in instance._changes_to_log:
            TaskHistory.objects.create(
                task=instance,
                changed_by=getattr(instance, '_changed_by', None),
                field_name=change['field_name'],
                old_value=change['old_value'],
                new_value=change['new_value']
            )
            
            # Додаємо системний коментар про зміну
            if change['old_value'] and change['new_value']:
                comment_text = (
                    f"{change['field_name']} змінено: "
                    f"{change['old_value']} → {change['new_value']}"
                )
            elif change['new_value']:
                comment_text = (
                    f"{change['field_name']} встановлено: {change['new_value']}"
                )
            else:
                comment_text = (
                    f"{change['field_name']} очищено"
                )
            
            TaskComment.objects.create(
                task=instance,
                author=getattr(instance, '_changed_by', None),
                text=comment_text,
                is_system=True
            )
        
        # Очищуємо атрибут
        delattr(instance, '_changes_to_log')


@receiver(post_save, sender=Project)
def create_default_statuses(sender, instance, created, **kwargs):
    """
    Створення стандартних статусів для нового проєкту
    якщо увімкнені власні статуси
    """
    if created and instance.use_custom_statuses:
        default_statuses = [
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
        
        for status_data in default_statuses:
            Status.objects.create(
                project=instance,
                **status_data
            )


def _format_field_value(field_name, value):
    """
    Форматування значення поля для читабельного відображення
    """
    if value is None:
        return "Не встановлено"
    
    if field_name == 'status':
        return str(value)
    elif field_name == 'assignee':
        return value.full_name if value else "Не призначено"
    elif field_name == 'priority':
        priority_names = {
            'low': 'Низький',
            'medium': 'Середній',
            'high': 'Високий',
            'critical': 'Критичний',
        }
        return priority_names.get(value, str(value))
    elif field_name == 'due_date':
        return value.strftime('%d.%m.%Y') if value else "Не встановлено"
    elif field_name == 'department':
        from .models import PersonGroup
        return dict(PersonGroup.choices).get(value, str(value)) if value else "Не встановлено"
    
    return str(value)


# Допоміжні функції для використання в views

def set_task_changed_by(task, person):
    """
    Встановлює користувача, який змінює завдання
    Використовуйте перед task.save()
    """
    task._changed_by = person


def bulk_update_task_status(tasks_queryset, new_status, changed_by=None):
    """
    Масове оновлення статусу завдань з логуванням
    """
    tasks = list(tasks_queryset)
    
    for task in tasks:
        old_status = task.status
        task.status = new_status
        
        if changed_by:
            task._changed_by = changed_by
        
        task.save()
        
        # Історія зміни
        TaskHistory.objects.create(
            task=task,
            changed_by=changed_by,
            field_name='Статус',
            old_value=str(old_status),
            new_value=str(new_status)
        )
    
    return len(tasks)


def get_overdue_tasks():
    """
    Отримати всі прострочені завдання
    """
    from django.db.models import Q
    today = timezone.now().date()
    
    return Task.objects.filter(
        Q(due_date__lt=today) &
        Q(is_completed=False)
    ).select_related('project', 'assignee', 'status')


def get_tasks_due_soon(days=7):
    """
    Отримати завдання, термін яких закінчується найближчим часом
    """
    from datetime import timedelta
    today = timezone.now().date()
    future_date = today + timedelta(days=days)
    
    return Task.objects.filter(
        due_date__range=[today, future_date],
        is_completed=False
    ).select_related('project', 'assignee', 'status').order_by('due_date')


def get_user_workload(person):
    """
    Отримати статистику навантаження користувача
    """
    from django.db.models import Count, Q
    
    tasks = Task.objects.filter(assignee=person)
    
    return {
        'total': tasks.count(),
        'active': tasks.filter(is_completed=False).count(),
        'completed': tasks.filter(is_completed=True).count(),
        'overdue': tasks.filter(
            Q(due_date__lt=timezone.now().date()) &
            Q(is_completed=False)
        ).count(),
        'by_priority': tasks.filter(is_completed=False).values('priority').annotate(
            count=Count('id')
        ),
        'by_project': tasks.filter(is_completed=False).values(
            'project__name'
        ).annotate(count=Count('id')),
    }


def get_project_statistics(project):
    """
    Отримати детальну статистику проєкту
    """
    from django.db.models import Count, Avg, Q
    from datetime import timedelta
    
    tasks = project.tasks.all()
    today = timezone.now().date()
    
    completed_tasks = tasks.filter(is_completed=True)
    active_tasks = tasks.filter(is_completed=False)
    
    # Середній час виконання
    avg_completion_time = None
    if completed_tasks.exists():
        completion_times = []
        for task in completed_tasks:
            if task.completed_at and task.created_at:
                delta = task.completed_at - task.created_at
                completion_times.append(delta.total_seconds() / 86400)  # в днях
        
        if completion_times:
            avg_completion_time = sum(completion_times) / len(completion_times)
    
    return {
        'total_tasks': tasks.count(),
        'completed': completed_tasks.count(),
        'active': active_tasks.count(),
        'overdue': active_tasks.filter(due_date__lt=today).count(),
        'due_this_week': active_tasks.filter(
            due_date__range=[today, today + timedelta(days=7)]
        ).count(),
        'by_status': tasks.values('status__name').annotate(
            count=Count('id')
        ).order_by('status__order'),
        'by_priority': active_tasks.values('priority').annotate(
            count=Count('id')
        ),
        'by_assignee': active_tasks.values('assignee__full_name').annotate(
            count=Count('id')
        ).order_by('-count')[:5],
        'avg_completion_days': round(avg_completion_time, 1) if avg_completion_time else None,
        'completion_rate': round(
            (completed_tasks.count() / tasks.count() * 100) if tasks.count() > 0 else 0,
            1
        ),
    }