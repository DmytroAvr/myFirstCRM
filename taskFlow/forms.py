from taskFlow.signals import (
    set_task_changed_by,           # Встановити автора змін
    bulk_update_task_status,       # Масове оновлення статусу
    get_overdue_tasks,             # Прострочені завдання
    get_tasks_due_soon,            # Завдання що скоро прострочаться
    get_user_workload,             # Навантаження користувача
    get_project_statistics,        # Статистика проєкту
)



# У view або формі
from oids.models import Person
from taskFlow.models import Task, Status
from taskFlow.signals import set_task_changed_by, get_user_workload

def update_task_view(request, task_id):
    task = Task.objects.get(pk=task_id)
    person = Person.objects.get(pk=request.user.person_id)  # Ваша логіка
    
    # Встановлюємо хто змінює
    set_task_changed_by(task, person)
    
    # Оновлюємо завдання
    task.status = Status.objects.get(name="В роботі")
    task.save()
    
    # Автоматично створюється запис в історії!
    return redirect('taskFlow:task_detail', pk=task.pk)


def user_dashboard(request):
    person = Person.objects.get(pk=request.user.person_id)
    
    # Отримуємо статистику користувача
    workload = get_user_workload(person)
    
    context = {
        'active_tasks': workload['active'],
        'overdue_tasks': workload['overdue'],
        'by_priority': workload['by_priority'],
    }
    
    return render(request, 'dashboard.html', context)



from taskFlow.signals import bulk_update_task_status

def close_project_tasks(request, project_id):
    project = Project.objects.get(pk=project_id)
    done_status = Status.objects.get(name="Виконано", project=None)
    person = Person.objects.get(pk=request.user.person_id)
    
    # Масово закриваємо всі завдання проєкту
    tasks = Task.objects.filter(project=project, is_completed=False)
    updated_count = bulk_update_task_status(tasks, done_status, person)
    
    messages.success(request, f'Закрито {updated_count} завдань')
    return redirect('taskFlow:project_detail', pk=project_id)

from taskFlow.signals import get_overdue_tasks, get_tasks_due_soon

def dashboard_view(request):
    # Прострочені завдання
    overdue = get_overdue_tasks()
    
    # Завдання на найближчі 7 днів
    due_soon = get_tasks_due_soon(days=7)
    
    # Завдання на завтра
    tomorrow_tasks = get_tasks_due_soon(days=1)
    
    context = {
        'overdue_count': overdue.count(),
        'due_soon_count': due_soon.count(),
        'overdue_tasks': overdue[:10],  # Перші 10
        'due_soon_tasks': due_soon,
    }
    
    return render(request, 'dashboard.html', context)

from taskFlow.signals import get_project_statistics

def project_report(request, project_id):
    project = Project.objects.get(pk=project_id)
    stats = get_project_statistics(project)
    
    context = {
        'project': project,
        'total_tasks': stats['total_tasks'],
        'completion_rate': stats['completion_rate'],
        'avg_completion_days': stats['avg_completion_days'],
        'by_status': stats['by_status'],
        'by_priority': stats['by_priority'],
        'top_assignees': stats['by_assignee'],
    }
    
    return render(request, 'taskFlow/project_report.html', context)