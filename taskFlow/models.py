"""
Django Task Manager Models
Система управління проєктами та завданнями
"""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from oids.models import PersonGroup, Person



class Project(models.Model):
    """
    Модель проєкту
    Представляє проєкт, який містить завдання
    """
    name = models.CharField(
        "Назва проєкту",
        max_length=255,
        unique=True,
        help_text="Унікальна назва проєкту"
    )
    key = models.CharField(
        "Ключ проєкту",
        max_length=10,
        unique=True,
        help_text="Короткий код проєкту (наприклад, PROJ, TASK)"
    )
    description = models.TextField(
        "Опис",
        blank=True,
        null=True,
        help_text="Детальний опис проєкту"
    )
    is_active = models.BooleanField(
        "Активний",
        default=True,
        help_text="Чи активний проєкт"
    )
    group = models.CharField(
        "Підрозділ",
        max_length=20,
        choices=PersonGroup.choices,
        default=PersonGroup.ZAG,
        help_text="Основний підрозділ проєкту"
    )
    use_custom_statuses = models.BooleanField(
        "Власні статуси",
        default=False,
        help_text="Використовувати власні статуси для цього проєкту"
    )
    created_at = models.DateTimeField(
        "Дата створення",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        "Дата оновлення",
        auto_now=True
    )

    class Meta:
        verbose_name = "Проєкт"
        verbose_name_plural = "Проєкти"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_active', '-created_at']),
            models.Index(fields=['key']),
        ]

    def __str__(self):
        return f"{self.name} ({self.key})"

    def clean(self):
        """Валідація моделі"""
        if self.key:
            self.key = self.key.upper()
        super().clean()

    def save(self, *args, **kwargs):
        """Перевизначення save для автоматичної валідації"""
        self.full_clean()
        super().save(*args, **kwargs)

    def get_tasks_count(self):
        """Загальна кількість завдань у проєкті"""
        return self.tasks.count()

    def get_active_tasks_count(self):
        """Кількість активних завдань"""
        return self.tasks.filter(is_completed=False).count()

    def get_completed_tasks_count(self):
        """Кількість виконаних завдань"""
        return self.tasks.filter(is_completed=True).count()


class Status(models.Model):
    """
    Модель статусу завдання
    Може бути глобальним або прив'язаним до конкретного проєкту
    """
    name = models.CharField(
        "Назва статусу",
        max_length=50,
        help_text="Назва статусу завдання"
    )
    color = models.CharField(
        "Колір",
        max_length=20,
        default="bg-gray-500",
        help_text="Клас кольору Tailwind CSS (наприклад, bg-blue-500)"
    )
    order = models.PositiveIntegerField(
        "Порядок",
        default=0,
        help_text="Порядок відображення статусу"
    )
    is_default = models.BooleanField(
        "Стандартний",
        default=False,
        help_text="Чи є цей статус стандартним для нових завдань"
    )
    is_final = models.BooleanField(
        "Фінальний статус",
        default=False,
        help_text="Чи означає цей статус завершення завдання"
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='custom_statuses',
        verbose_name="Проєкт",
        help_text="Проєкт (якщо порожньо - глобальний статус)"
    )
    created_at = models.DateTimeField(
        "Дата створення",
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Статус завдання"
        verbose_name_plural = "Статуси завдань"
        ordering = ['project', 'order', 'name']
        unique_together = [['name', 'project']]
        indexes = [
            models.Index(fields=['project', 'order']),
        ]

    def __str__(self):
        if self.project:
            return f"{self.name} ({self.project.key})"
        return f"{self.name} (Глобальний)"

    def clean(self):
        """Валідація: тільки один стандартний статус на проєкт"""
        if self.is_default:
            existing = Status.objects.filter(
                project=self.project,
                is_default=True
            ).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(
                    "Вже існує стандартний статус для цього проєкту"
                )
        super().clean()


class Task(models.Model):
    """
    Модель завдання
    Основна одиниця роботи в системі
    """
    PRIORITY_CHOICES = [
        ('low', 'Низький'),
        ('medium', 'Середній'),
        ('high', 'Високий'),
        ('critical', 'Критичний'),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks',
        verbose_name="Проєкт"
    )
    key = models.CharField(
        "Ключ завдання",
        max_length=20,
        unique=True,
        editable=False,
        help_text="Автоматично генерується (наприклад, PROJ-123)"
    )
    title = models.CharField(
        "Заголовок",
        max_length=255,
        help_text="Коротка назва завдання"
    )
    description = models.TextField(
        "Опис",
        blank=True,
        null=True,
        help_text="Детальний опис завдання"
    )
    assignee = models.ForeignKey('oids.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taskflow_assigned_tasks',
        verbose_name="Виконавець",
        help_text="Особа, відповідальна за виконання"
    )
    department = models.CharField(
        "Підрозділ",
        max_length=20,
        choices=PersonGroup.choices,
        blank=True,
        null=True,
        help_text="Підрозділ, відповідальний за завдання"
    )
    due_date = models.DateField(
        "Термін виконання",
        null=True,
        blank=True,
        help_text="Дедлайн для виконання завдання"
    )
    created_by = models.ForeignKey(
        'oids.Person',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='taskflow_created_tasks',
        verbose_name="Автор",
        help_text="Хто створив завдання"
    )
    status = models.ForeignKey(
        Status,
        on_delete=models.PROTECT,
        related_name='tasks',
        verbose_name="Поточний статус"
    )
    priority = models.CharField(
        "Пріоритет",
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text="Пріоритет виконання завдання"
    )
    is_completed = models.BooleanField(
        "Виконано",
        default=False,
        help_text="Чи виконано завдання"
    )
    completed_at = models.DateTimeField(
        "Дата виконання",
        null=True,
        blank=True,
        help_text="Коли завдання було виконано"
    )
    created_at = models.DateTimeField(
        "Дата створення",
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        "Дата оновлення",
        auto_now=True
    )

    class Meta:
        verbose_name = "Завдання"
        verbose_name_plural = "Завдання"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['assignee', 'is_completed']),
            models.Index(fields=['due_date']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.key}: {self.title}"

    def save(self, *args, **kwargs):
        """Автоматична генерація ключа та обробка статусу"""
        # Генерація ключа при створенні
        if not self.key:
            # Отримуємо наступний номер для проєкту
            last_task = Task.objects.filter(
                project=self.project
            ).order_by('-created_at').first()
            
            if last_task and last_task.key:
                # Витягуємо номер з останнього ключа
                try:
                    last_number = int(last_task.key.split('-')[-1])
                    next_number = last_number + 1
                except (ValueError, IndexError):
                    next_number = 1
            else:
                next_number = 1
            
            self.key = f"{self.project.key}-{next_number}"

        # Автоматичне встановлення статусу "виконано"
        if self.status and self.status.is_final and not self.is_completed:
            self.is_completed = True
            self.completed_at = timezone.now()
        elif not self.status or not self.status.is_final:
            if self.is_completed:
                self.is_completed = False
                self.completed_at = None

        super().save(*args, **kwargs)

    def is_overdue(self):
        """Чи прострочене завдання"""
        if not self.due_date or self.is_completed:
            return False
        return timezone.now().date() > self.due_date

    def is_due_today(self):
        """Чи термін виконання сьогодні"""
        if not self.due_date or self.is_completed:
            return False
        return timezone.now().date() == self.due_date

    def get_priority_color(self):
        """Отримати колір пріоритету"""
        colors = {
            'low': 'text-gray-600',
            'medium': 'text-yellow-600',
            'high': 'text-orange-600',
            'critical': 'text-red-600',
        }
        return colors.get(self.priority, 'text-gray-600')
    
    def should_be_archived(self):
        """
        Перевіряє чи завдання має бути заархівоване
        Завдання архівується якщо воно виконане та пройшло 8:10 наступного дня
        """
        if not self.is_completed or not self.completed_at:
            return False
        
        # Отримуємо дату та час виконання
        completed_datetime = self.completed_at
        
        # Обчислюємо наступний день о 8:10
        archive_time = completed_datetime.replace(
            hour=8, 
            minute=10, 
            second=0, 
            microsecond=0
        )
        
        # Якщо виконано після 8:10, то архівація буде наступного дня о 8:10
        if completed_datetime.hour >= 8 and completed_datetime.minute >= 10:
            archive_time = archive_time + timezone.timedelta(days=1)
        # Якщо виконано до 8:10, то архівація буде сьогодні о 8:10
        # але якщо зараз вже після 8:10, то наступного дня
        else:
            if timezone.now() >= archive_time:
                archive_time = archive_time + timezone.timedelta(days=1)
        
        # Перевіряємо чи настав час архівації
        return timezone.now() >= archive_time
    
    def is_recently_completed(self):
        """
        Перевіряє чи завдання щойно виконане (ще не архівоване)
        """
        return self.is_completed and not self.should_be_archived()



class TaskComment(models.Model):
    """
    Модель коментаря до завдання
    Для обговорення та історії змін
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Завдання"
    )
    author = models.ForeignKey(
        'oids.Person',
        on_delete=models.SET_NULL,
        null=True,
        related_name='comments',
        verbose_name="Автор"
    )
    text = models.TextField(
        "Текст коментаря",
        help_text="Коментар або примітка"
    )
    is_system = models.BooleanField(
        "Системний",
        default=False,
        help_text="Чи є це системний коментар (автоматична зміна)"
    )
    created_at = models.DateTimeField(
        "Дата створення",
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Коментар"
        verbose_name_plural = "Коментарі"
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['task', 'created_at']),
        ]

    def __str__(self):
        return f"Коментар до {self.task.key} від {self.author}"


class TaskHistory(models.Model):
    """
    Модель історії змін завдання
    Відстежує всі зміни статусу, виконавця тощо
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name="Завдання"
    )
    changed_by = models.ForeignKey(
        'oids.Person',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Хто змінив"
    )
    field_name = models.CharField(
        "Поле",
        max_length=50,
        help_text="Назва зміненого поля"
    )
    old_value = models.TextField(
        "Старе значення",
        blank=True,
        null=True
    )
    new_value = models.TextField(
        "Нове значення",
        blank=True,
        null=True
    )
    changed_at = models.DateTimeField(
        "Дата зміни",
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Історія змін"
        verbose_name_plural = "Історія змін"
        ordering = ['-changed_at']
        indexes = [
            models.Index(fields=['task', '-changed_at']),
        ]

    def __str__(self):
        return f"{self.task.key}: {self.field_name} змінено {self.changed_at}"