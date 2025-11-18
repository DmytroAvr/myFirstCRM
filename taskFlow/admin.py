"""
Django Admin Configuration для Task Manager
Налаштування адміністративної панелі
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from django.utils import timezone
from .models import Person, Project, Status, Task, TaskComment, TaskHistory


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    """Адміністрування виконавців"""
    list_display = [
        'full_name', 'position', 'group_badge', 
        'active_tasks_count', 'is_active_badge', 'created_at'
    ]
    list_filter = ['group', 'is_active', 'created_at']
    search_fields = ['full_name', 'surname', 'position']
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('full_name', 'surname', 'position')
        }),
        ('Організаційна структура', {
            'fields': ('group', 'is_active')
        }),
        ('Метадані', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def group_badge(self, obj):
        """Відображення підрозділу з кольоровим бейджем"""
        colors = {
            'management': '#3b82f6',
            'zbsi': '#10b981',
            'iarm': '#f59e0b',
            'sd_ktk': '#8b5cf6',
            'workshop': '#ef4444',
            'pdtr': '#ec4899',
            'sl': '#06b6d4',
        }
        color = colors.get(obj.group, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_group_display()
        )
    group_badge.short_description = 'Підрозділ'
    
    def is_active_badge(self, obj):
        """Відображення статусу активності"""
        if obj.is_active:
            return format_html(
                '<span style="color: green;">✓ Активний</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Неактивний</span>'
        )
    is_active_badge.short_description = 'Статус'
    
    def active_tasks_count(self, obj):
        """Кількість активних завдань"""
        count = obj.get_active_tasks_count()
        if count > 0:
            return format_html(
                '<strong style="color: #f59e0b;">{}</strong>', count
            )
        return count
    active_tasks_count.short_description = 'Активні завдання'
    
    actions = ['activate_persons', 'deactivate_persons']
    
    def activate_persons(self, request, queryset):
        """Активувати виконавців"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активовано {updated} виконавців')
    activate_persons.short_description = 'Активувати виконавців'
    
    def deactivate_persons(self, request, queryset):
        """Деактивувати виконавців"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивовано {updated} виконавців')
    deactivate_persons.short_description = 'Деактивувати виконавців'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Адміністрування проєктів"""
    list_display = [
        'name', 'key_badge', 'group_badge', 
        'tasks_stats', 'is_active_badge', 'created_at'
    ]
    list_filter = ['is_active', 'group', 'use_custom_statuses', 'created_at']
    search_fields = ['name', 'key', 'description']
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('name', 'key', 'description')
        }),
        ('Налаштування', {
            'fields': ('group', 'is_active', 'use_custom_statuses')
        }),
        ('Метадані', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def key_badge(self, obj):
        """Відображення ключа проєкту"""
        return format_html(
            '<code style="background-color: #f3f4f6; padding: 2px 8px; '
            'border-radius: 4px; font-weight: bold;">{}</code>',
            obj.key
        )
    key_badge.short_description = 'Ключ'
    
    def group_badge(self, obj):
        """Відображення підрозділу"""
        colors = {
            'management': '#3b82f6',
            'zbsi': '#10b981',
            'iarm': '#f59e0b',
            'sd_ktk': '#8b5cf6',
            'workshop': '#ef4444',
            'pdtr': '#ec4899',
            'sl': '#06b6d4',
        }
        color = colors.get(obj.group, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 12px; font-size: 11px;">{}</span>',
            color, obj.get_group_display()
        )
    group_badge.short_description = 'Підрозділ'
    
    def tasks_stats(self, obj):
        """Статистика завдань"""
        total = obj.get_tasks_count()
        active = obj.get_active_tasks_count()
        completed = obj.get_completed_tasks_count()
        return format_html(
            '<span style="color: #3b82f6;">Всього: {}</span> | '
            '<span style="color: #f59e0b;">Активні: {}</span> | '
            '<span style="color: #10b981;">Виконані: {}</span>',
            total, active, completed
        )
    tasks_stats.short_description = 'Статистика завдань'
    
    def is_active_badge(self, obj):
        """Відображення статусу активності"""
        if obj.is_active:
            return format_html(
                '<span style="color: green;">✓ Активний</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Неактивний</span>'
        )
    is_active_badge.short_description = 'Статус'
    
    actions = ['activate_projects', 'deactivate_projects']
    
    def activate_projects(self, request, queryset):
        """Активувати проєкти"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активовано {updated} проєктів')
    activate_projects.short_description = 'Активувати проєкти'
    
    def deactivate_projects(self, request, queryset):
        """Деактивувати проєкти"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивовано {updated} проєктів')
    deactivate_projects.short_description = 'Деактивувати проєкти'


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    """Адміністрування статусів"""
    list_display = [
        'name', 'color_preview', 'project_display', 
        'order', 'is_default', 'is_final', 'tasks_count'
    ]
    list_filter = ['is_default', 'is_final', 'project']
    search_fields = ['name']
    list_editable = ['order']
    list_per_page = 50
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('name', 'color', 'project')
        }),
        ('Налаштування', {
            'fields': ('order', 'is_default', 'is_final')
        }),
    )
    
    def color_preview(self, obj):
        """Попередній перегляд кольору"""
        color_map = {
            'bg-gray-500': '#6b7280',
            'bg-blue-500': '#3b82f6',
            'bg-green-500': '#10b981',
            'bg-yellow-500': '#eab308',
            'bg-orange-500': '#f97316',
            'bg-red-500': '#ef4444',
            'bg-purple-500': '#a855f7',
            'bg-pink-500': '#ec4899',
            'bg-indigo-500': '#6366f1',
            'bg-teal-500': '#14b8a6',
        }
        hex_color = color_map.get(obj.color, '#6b7280')
        return format_html(
            '<div style="width: 60px; height: 20px; background-color: {}; '
            'border-radius: 4px; border: 1px solid #ddd;"></div>',
            hex_color
        )
    color_preview.short_description = 'Колір'
    
    def project_display(self, obj):
        """Відображення проєкту"""
        if obj.project:
            return format_html(
                '<span style="background-color: #dbeafe; color: #1e40af; '
                'padding: 3px 8px; border-radius: 12px; font-size: 11px;">{}</span>',
                obj.project.key
            )
        return format_html(
            '<span style="color: #6b7280; font-style: italic;">Глобальний</span>'
        )
    project_display.short_description = 'Проєкт'
    
    def tasks_count(self, obj):
        """Кількість завдань з цим статусом"""
        count = obj.tasks.count()
        if count > 0:
            return format_html(
                '<strong style="color: #3b82f6;">{}</strong>', count
            )
        return count
    tasks_count.short_description = 'Завдань'


class TaskCommentInline(admin.TabularInline):
    """Inline для коментарів"""
    model = TaskComment
    extra = 0
    fields = ['author', 'text', 'is_system', 'created_at']
    readonly_fields = ['created_at']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Адміністрування завдань"""
    list_display = [
        'key_display', 'title_display', 'project', 
        'status_badge', 'priority_badge', 'assignee',
        'due_date_display', 'is_completed'
    ]
    list_filter = [
        'is_completed', 'priority', 'project', 
        'status', 'department', 'created_at'
    ]
    search_fields = ['key', 'title', 'description']
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('project', 'key', 'title', 'description')
        }),
        ('Призначення та виконання', {
            'fields': (
                'assignee', 'department', 'created_by', 
                'status', 'priority', 'due_date'
            )
        }),
        ('Статус виконання', {
            'fields': ('is_completed', 'completed_at'),
            'classes': ('collapse',)
        }),
        ('Метадані', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['key', 'created_at', 'updated_at', 'completed_at']
    inlines = [TaskCommentInline]
    
    def key_display(self, obj):
        """Відображення ключа завдання"""
        return format_html(
            '<code style="background-color: #f3f4f6; padding: 2px 8px; '
            'border-radius: 4px; font-weight: bold; color: #1e40af;">{}</code>',
            obj.key
        )
    key_display.short_description = 'Ключ'
    
    def title_display(self, obj):
        """Відображення заголовка з відміткою про прострочення"""
        if obj.is_overdue():
            return format_html(
                '<span style="color: #dc2626;">⚠ {}</span>', obj.title
            )
        elif obj.is_due_today():
            return format_html(
                '<span style="color: #f97316;">⏰ {}</span>', obj.title
            )
        return obj.title
    title_display.short_description = 'Заголовок'
    
    def status_badge(self, obj):
        """Відображення статусу"""
        color_map = {
            'bg-gray-500': '#6b7280',
            'bg-blue-500': '#3b82f6',
            'bg-green-500': '#10b981',
            'bg-yellow-500': '#eab308',
            'bg-orange-500': '#f97316',
            'bg-red-500': '#ef4444',
            'bg-purple-500': '#a855f7',
            'bg-pink-500': '#ec4899',
        }
        hex_color = color_map.get(obj.status.color, '#6b7280')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 10px; border-radius: 12px; font-size: 11px;">{}</span>',
            hex_color, obj.status.name
        )
    status_badge.short_description = 'Статус'
    
    def priority_badge(self, obj):
        """Відображення пріоритету"""
        colors = {
            'low': '#6b7280',
            'medium': '#eab308',
            'high': '#f97316',
            'critical': '#dc2626',
        }
        color = colors.get(obj.priority, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_priority_display()
        )
    priority_badge.short_description = 'Пріоритет'
    
    def due_date_display(self, obj):
        """Відображення терміну виконання"""
        if not obj.due_date:
            return '—'
        
        if obj.is_overdue():
            return format_html(
                '<span style="color: #dc2626; font-weight: bold;">⚠ {}</span>',
                obj.due_date.strftime('%d.%m.%Y')
            )
        elif obj.is_due_today():
            return format_html(
                '<span style="color: #f97316; font-weight: bold;">⏰ {}</span>',
                obj.due_date.strftime('%d.%m.%Y')
            )
        return obj.due_date.strftime('%d.%m.%Y')
    due_date_display.short_description = 'Термін'
    
    actions = ['mark_as_completed', 'mark_as_incomplete']
    
    def mark_as_completed(self, request, queryset):
        """Позначити як виконані"""
        updated = queryset.filter(is_completed=False).update(
            is_completed=True,
            completed_at=timezone.now()
        )
        self.message_user(request, f'Виконано {updated} завдань')
    mark_as_completed.short_description = 'Позначити як виконані'
    
    def mark_as_incomplete(self, request, queryset):
        """Позначити як невиконані"""
        updated = queryset.filter(is_completed=True).update(
            is_completed=False,
            completed_at=None
        )
        self.message_user(request, f'Повернуто {updated} завдань')
    mark_as_incomplete.short_description = 'Позначити як невиконані'


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    """Адміністрування коментарів"""
    list_display = ['task', 'author', 'text_preview', 'is_system', 'created_at']
    list_filter = ['is_system', 'created_at']
    search_fields = ['task__key', 'text']
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    def text_preview(self, obj):
        """Попередній перегляд тексту"""
        max_length = 100
        if len(obj.text) > max_length:
            return f"{obj.text[:max_length]}..."
        return obj.text
    text_preview.short_description = 'Текст'


@admin.register(TaskHistory)
class TaskHistoryAdmin(admin.ModelAdmin):
    """Адміністрування історії змін"""
    list_display = [
        'task', 'field_name', 'old_value_preview', 
        'new_value_preview', 'changed_by', 'changed_at'
    ]
    list_filter = ['field_name', 'changed_at']
    search_fields = ['task__key', 'field_name']
    list_per_page = 50
    date_hierarchy = 'changed_at'
    
    def old_value_preview(self, obj):
        """Попередній перегляд старого значення"""
        if not obj.old_value:
            return '—'
        max_length = 50
        if len(obj.old_value) > max_length:
            return f"{obj.old_value[:max_length]}..."
        return obj.old_value
    old_value_preview.short_description = 'Старе значення'
    
    def new_value_preview(self, obj):
        """Попередній перегляд нового значення"""
        if not obj.new_value:
            return '—'
        max_length = 50
        if len(obj.new_value) > max_length:
            return f"{obj.new_value[:max_length]}..."
        return obj.new_value
    new_value_preview.short_description = 'Нове значення'