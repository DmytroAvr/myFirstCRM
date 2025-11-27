"""
Views для TaskFlow
Повна версія з інтеграцією User → Person
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from oids.models import Person, PersonGroup
from .models import Project, Task, Status, TaskComment
from .signals import (
    set_task_changed_by,
    get_overdue_tasks,
    get_tasks_due_soon,
    get_user_workload,
    get_project_statistics,
)


# ==================== HELPER ФУНКЦІЇ ====================

def get_current_person(request):
    """
    Отримати поточного Person з request
    Підтримує 3 варіанти:
    1. request.person (якщо є middleware)
    2. Person.user (якщо є поле user в моделі)
    3. Person.email (пошук по email)
    
    Returns:
        Person object or None
    """
    # Варіант 1: Якщо є middleware
    if hasattr(request, 'person'):
        return request.person
    
    if not request.user.is_authenticated:
        return None
    
    # Варіант 2: Якщо є поле user в Person
    try:
        return Person.objects.get(user=request.user, is_active=True)
    except (Person.DoesNotExist, AttributeError):
        pass
    
    # Варіант 3: Пошук по email
    try:
        return Person.objects.get(email=request.user.email, is_active=True)
    except (Person.DoesNotExist, AttributeError):
        pass
    
    return None


def require_person(view_func):
    """
    Декоратор для перевірки наявності Person
    """
    def wrapper(request, *args, **kwargs):
        person = get_current_person(request)
        if not person:
            messages.error(
                request, 
                'Ваш обліковий запис не зв\'язано з виконавцем. '
                'Зверніться до адміністратора.'
            )
            return redirect('taskFlow:project_list')
        return view_func(request, *args, **kwargs)
    return wrapper


# ==================== ПРОЄКТИ ====================

@login_required
def project_list(request):
    """Список проєктів"""
    projects = Project.objects.filter(is_active=True).annotate(
        task_count=Count('tasks'),
        active_task_count=Count('tasks', filter=Q(tasks__is_completed=False))
    ).order_by('-created_at')
    
    context = {
        'projects': projects,
        'overdue_tasks': get_overdue_tasks().count(),
        'due_soon_tasks': get_tasks_due_soon().count(),
        'current_person': get_current_person(request),
    }
    
    return render(request, 'taskFlow/project_list.html', context)


@login_required
def project_detail(request, pk):
    """Детальна інформація про проєкт"""
    project = get_object_or_404(Project, pk=pk)
    statistics = get_project_statistics(project)
    
    context = {
        'project': project,
        'statistics': statistics,
        'current_person': get_current_person(request),
    }
    
    return render(request, 'taskFlow/project_detail.html', context)


@login_required
def project_board(request, pk):
    """Канбан-дошка проєкту"""
    project = get_object_or_404(Project, pk=pk)
    
    # Отримуємо статуси (власні або глобальні)
    if project.use_custom_statuses:
        statuses = project.custom_statuses.all().order_by('order')
    else:
        statuses = Status.objects.filter(project=None).order_by('order')
    
    # Формуємо дані для кожного статусу
    board_data = []
    for status in statuses:
        # Отримуємо всі завдання зі статусом
        all_tasks = Task.objects.filter(
            project=project,
            status=status
        ).select_related('assignee', 'created_by').prefetch_related('comments')
        
        # Фільтруємо: показуємо незавершені + щойно завершені (до архівації)
        visible_tasks = [
            task for task in all_tasks 
            if not task.is_completed or task.is_recently_completed()
        ]
        
        board_data.append({
            'status': status,
            'tasks': visible_tasks,
            'count': len(visible_tasks),
        })
    
    # Отримуємо всіх виконавців для фільтра
    persons = Person.objects.filter(is_active=True)
    
    context = {
        'project': project,
        'board_data': board_data,
        'persons': persons,
        'current_person': get_current_person(request),
    }
    
    return render(request, 'taskFlow/project_board.html', context)


# ==================== ЗАВДАННЯ ====================

@login_required
def task_list(request):
    """Список завдань з фільтрацією"""
    tasks = Task.objects.select_related(
        'project', 'assignee', 'status', 'created_by'
    )
    
    # Фільтрація
    project_id = request.GET.get('project')
    if project_id:
        tasks = tasks.filter(project_id=project_id)
    
    status_id = request.GET.get('status')
    if status_id:
        tasks = tasks.filter(status_id=status_id)
    
    assignee_id = request.GET.get('assignee')
    if assignee_id:
        tasks = tasks.filter(assignee_id=assignee_id)
    
    priority = request.GET.get('priority')
    if priority:
        tasks = tasks.filter(priority=priority)
    
    show_completed = request.GET.get('completed')
    if not show_completed:
        tasks = tasks.filter(is_completed=False)
    
    # Пошук
    search = request.GET.get('q')
    if search:
        tasks = tasks.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(key__icontains=search)
        )
    
    context = {
        'tasks': tasks.order_by('-created_at'),
        'projects': Project.objects.filter(is_active=True),
        'statuses': Status.objects.filter(project=None),
        'persons': Person.objects.filter(is_active=True),
        'current_person': get_current_person(request),
    }
    
    return render(request, 'taskFlow/task_list.html', context)


@login_required
def task_detail(request, pk):
    """Детальна інформація про завдання"""
    task = get_object_or_404(
        Task.objects.select_related(
            'project', 'assignee', 'status', 'created_by'
        ),
        pk=pk
    )
    
    # Отримання поточного користувача
    person = get_current_person(request)
    
    # Обробка POST запитів
    if request.method == 'POST':
        # Перевірка наявності Person для дій
        if not person:
            messages.error(
                request, 
                'Не вдалося визначити вашого виконавця. '
                'Перегляд доступний, але дії заборонені.'
            )
            return redirect('taskFlow:task_detail', pk=pk)
        
        # Додавання коментаря
        if 'add_comment' in request.POST:
            comment_text = request.POST.get('comment_text', '').strip()
            if comment_text:
                TaskComment.objects.create(
                    task=task,
                    author=person,
                    text=comment_text,
                    is_system=False
                )
                messages.success(request, 'Коментар додано')
                return redirect('taskFlow:task_detail', pk=pk)
        
        # Позначити як виконане
        if 'mark_completed' in request.POST:
            set_task_changed_by(task, person)
            
            # Знаходимо фінальний статус
            final_status = Status.objects.filter(
                Q(project=task.project) | Q(project=None),
                is_final=True
            ).first()
            
            if final_status:
                task.status = final_status
                task.is_completed = True
                task.completed_at = timezone.now()
                task.save()
                messages.success(request, f'Завдання {task.key} виконано')
            else:
                messages.error(request, 'Не знайдено фінальний статус')
            
            return redirect('taskFlow:task_detail', pk=pk)
    
    # Коментарі
    comments = task.comments.select_related('author').order_by('created_at')
    
    # Історія
    history = task.history.select_related('changed_by').order_by('-changed_at')[:20]
    
    context = {
        'task': task,
        'comments': comments,
        'history': history,
        'current_person': person,
        'can_edit': person is not None,
    }
    
    return render(request, 'taskFlow/task_detail.html', context)


@login_required
@require_person
def task_create(request):
    """Створення нового завдання"""
    person = get_current_person(request)
    
    if request.method == 'POST':
        # Отримуємо дані з форми
        project_id = request.POST.get('project')
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        assignee_id = request.POST.get('assignee')
        department = request.POST.get('department')
        priority = request.POST.get('priority', 'medium')
        status_id = request.POST.get('status')
        due_date = request.POST.get('due_date')
        
        # Валідація
        if not project_id or not title:
            messages.error(request, 'Заповніть обов\'язкові поля: Проєкт та Назва')
            return redirect('taskFlow:task_create')
        
        try:
            project = Project.objects.get(pk=project_id)
            
            # Отримуємо статус
            if status_id:
                status = Status.objects.get(pk=status_id)
            else:
                # Беремо стандартний статус
                status = Status.objects.filter(
                    Q(project=project) | Q(project=None),
                    is_default=True
                ).first()
                
                if not status:
                    status = Status.objects.filter(
                        Q(project=project) | Q(project=None)
                    ).first()
            
            # Отримуємо виконавця
            assignee = Person.objects.get(pk=assignee_id) if assignee_id else None
            
            # Створюємо завдання
            task = Task.objects.create(
                project=project,
                title=title,
                description=description,
                assignee=assignee,
                department=department if department else None,
                priority=priority,
                status=status,
                due_date=due_date if due_date else None,
                created_by=person  # Використовуємо поточного Person
            )
            
            messages.success(request, f'Завдання {task.key} створено успішно')
            return redirect('taskFlow:task_detail', pk=task.pk)
            
        except Project.DoesNotExist:
            messages.error(request, 'Проєкт не знайдено')
        except Status.DoesNotExist:
            messages.error(request, 'Статус не знайдено')
        except Person.DoesNotExist:
            messages.error(request, 'Виконавця не знайдено')
        except Exception as e:
            messages.error(request, f'Помилка створення завдання: {str(e)}')
        
        return redirect('taskFlow:task_create')
    
    # GET запит - показуємо форму
    projects = Project.objects.filter(is_active=True)
    persons = Person.objects.filter(is_active=True)
    statuses = Status.objects.filter(project=None)
    
    # Pre-fill з параметрів URL
    selected_project = request.GET.get('project')
    selected_status = request.GET.get('status')
    
    context = {
        'projects': projects,
        'persons': persons,
        'statuses': statuses,
        'selected_project': selected_project,
        'selected_status': selected_status,
        'priorities': Task.PRIORITY_CHOICES,
        'departments': PersonGroup.choices,
        'current_person': person,
    }
    
    return render(request, 'taskFlow/task_form.html', context)


@login_required
@require_person
def task_edit(request, pk):
    """Редагування завдання"""
    task = get_object_or_404(Task, pk=pk)
    person = get_current_person(request)
    
    if request.method == 'POST':
        # Встановлюємо хто змінює
        set_task_changed_by(task, person)
        
        # Оновлюємо поля
        task.title = request.POST.get('title', task.title).strip()
        task.description = request.POST.get('description', '').strip()
        
        # Виконавець
        assignee_id = request.POST.get('assignee')
        task.assignee = Person.objects.get(pk=assignee_id) if assignee_id else None
        
        # Підрозділ
        department = request.POST.get('department')
        task.department = department if department else None
        
        # Пріоритет
        task.priority = request.POST.get('priority', task.priority)
        
        # Статус
        status_id = request.POST.get('status')
        if status_id:
            task.status = Status.objects.get(pk=status_id)
        
        # Термін
        due_date_str = request.POST.get('due_date')
        if due_date_str:
            try:
                from datetime import datetime
                task.due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.warning(request, 'Неправильний формат дати')
        else:
            task.due_date = None
        
        try:
            task.save()
            messages.success(request, f'Завдання {task.key} оновлено')
            return redirect('taskFlow:task_detail', pk=task.pk)
        except Exception as e:
            messages.error(request, f'Помилка оновлення: {str(e)}')
            return redirect('taskFlow:task_edit', pk=pk)
    
    # GET - показуємо форму
    projects = Project.objects.filter(is_active=True)
    persons = Person.objects.filter(is_active=True)
    
    # Статуси для проєкту
    if task.project.use_custom_statuses:
        statuses = task.project.custom_statuses.all()
    else:
        statuses = Status.objects.filter(project=None)
    
    context = {
        'task': task,
        'projects': projects,
        'persons': persons,
        'statuses': statuses,
        'priorities': Task.PRIORITY_CHOICES,
        'departments': PersonGroup.choices,
        'is_edit': True,
        'current_person': person,
    }
    
    return render(request, 'taskFlow/task_form.html', context)


@login_required
@require_person
def task_delete(request, pk):
    """Видалення завдання"""
    task = get_object_or_404(Task, pk=pk)
    
    if request.method == 'POST':
        project_id = task.project.id
        task_key = task.key
        
        try:
            task.delete()
            messages.success(request, f'Завдання {task_key} видалено')
            return redirect('taskFlow:project_detail', pk=project_id)
        except Exception as e:
            messages.error(request, f'Помилка видалення: {str(e)}')
            return redirect('taskFlow:task_detail', pk=pk)
    
    # Якщо не POST - перенаправляємо на деталі
    return redirect('taskFlow:task_detail', pk=pk)


# ==================== API ====================

@login_required
@require_http_methods(["POST"])
def task_update_status(request, pk):
    """API: Оновлення статусу завдання"""
    task = get_object_or_404(Task, pk=pk)
    new_status_id = request.POST.get('status_id')
    
    # Отримуємо поточного користувача
    person = get_current_person(request)
    
    if not person:
        return JsonResponse({
            'success': False,
            'error': 'Не вдалося визначити поточного виконавця'
        }, status=403)
    
    try:
        new_status = Status.objects.get(pk=new_status_id)
        
        # Встановлюємо автора змін
        set_task_changed_by(task, person)
        
        # Оновлюємо статус
        task.status = new_status
        task.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Статус оновлено',
            'task_key': task.key,
            'new_status': new_status.name,
        })
    
    except Status.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Статус не знайдено'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def task_assign(request, pk):
    """API: Призначення виконавця"""
    task = get_object_or_404(Task, pk=pk)
    assignee_id = request.POST.get('assignee_id')
    
    # Отримуємо поточного користувача
    person = get_current_person(request)
    
    if not person:
        return JsonResponse({
            'success': False,
            'error': 'Не вдалося визначити поточного виконавця'
        }, status=403)
    
    try:
        assignee = Person.objects.get(pk=assignee_id) if assignee_id else None
        
        # Встановлюємо автора змін
        set_task_changed_by(task, person)
        
        # Оновлюємо виконавця
        task.assignee = assignee
        task.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Виконавця призначено',
            'assignee': assignee.full_name if assignee else 'Не призначено',
        })
    
    except Person.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Виконавця не знайдено'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# ==================== ДОДАТКОВІ VIEW ====================

@login_required
def dashboard(request):
    """Головна дашборд сторінка"""
    person = get_current_person(request)
    
    # Статистика користувача
    workload = get_user_workload(person) if person else None
    
    # Прострочені та найближчі завдання
    overdue_tasks = get_overdue_tasks()[:10]
    due_soon_tasks = get_tasks_due_soon(days=7)
    
    context = {
        'person': person,
        'workload': workload,
        'overdue_tasks': overdue_tasks,
        'due_soon_tasks': due_soon_tasks,
        'current_person': person,
    }
    
    return render(request, 'taskFlow/dashboard.html', context)