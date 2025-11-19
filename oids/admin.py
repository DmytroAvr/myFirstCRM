from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin 
from django.utils.html import format_html
from django.db.models import Count, Q
from django.utils import timezone
from .models import (
    TerritorialManagement, UnitGroup, Unit, OID,
    Person, WorkRequest, WorkRequestItem,
    DocumentType, Document, Trip, OIDStatusChange,
    TripResultForUnit, TechnicalTask, 
    AttestationRegistration, AttestationResponse,
    WorkCompletionRegistration, WorkCompletionResponse,
    Declaration, DeclarationRegistration,
    OIDProcess, OIDProcessStepInstance, ProcessTemplate, ProcessStep, OIDStatusChoices
)



@admin.register(TerritorialManagement)
class TerritorialManagementAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


@admin.register(UnitGroup)
class UnitGroupAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Unit)
class UnitAdmin(SimpleHistoryAdmin):
    list_display = ('code', 'name', 'city', 'territorial_management')
    search_fields = ('code', 'name', 'city')
    list_filter = ('territorial_management', 'unit_groups')



@admin.register(OID)
class OIDAdmin(SimpleHistoryAdmin):
    # ✅ Покращене відображення списку
    list_display = (
        'cipher', 
        'colored_status',  # Кастомний метод з кольорами
        'oid_type', 
        'unit_link',  # Клікабельне посилання
        'room', 
        'sec_level',
        'is_active',
        'documents_count_display',  # Кількість документів
        'created_at_short'
    )
    
    # ✅ Можливість швидкого редагування зі списку
    list_editable = ('is_active',)
    
    # ✅ Розширені фільтри
    list_filter = (
        'is_active',
        'oid_type',
        'status',
        'sec_level',
        ('unit', admin.RelatedOnlyFieldListFilter),  # Тільки частини що мають ОІД
        ('created_at', admin.DateFieldListFilter),
        'pemin_sub_type',
    )
    
    # ✅ Покращений пошук
    search_fields = (
        'cipher', 
        'full_name', 
        'room',
        'serial_number',
        'inventory_number',
        'unit__code',
        'unit__name'
    )
    
    # ✅ Автозаповнення для ForeignKey (швидше ніж dropdown)
    autocomplete_fields = ['unit']
    
    # ✅ Організація полів у вкладки
    fieldsets = (
        ('Основна інформація', {
            'fields': (
                'unit',
                ('cipher', 'is_active'),
                'full_name',
                ('oid_type', 'pemin_sub_type'),
            )
        }),
        ('Класифікація та розташування', {
            'fields': (
                ('sec_level', 'room'),
                ('serial_number', 'inventory_number'),
            )
        }),
        ('Статус та примітки', {
            'fields': (
                'status',
                'note',
            )
        }),
        ('Системна інформація', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),  # Згорнуто за замовчуванням
        }),
    )
    
    # ✅ Поля тільки для читання
    readonly_fields = ('created_at', 'updated_at', 'documents_count_display')
    
    # ✅ Сортування за замовчуванням
    ordering = ('-created_at',)
    
    # ✅ Навігація по датах
    date_hierarchy = 'created_at'
    
    # ✅ Кількість записів на сторінці
    list_per_page = 50
    
    # ✅ Пошук в історії
    history_list_display = ["status", "is_active", "room"]
    
    # ✅ Оптимізація запитів
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # Завантажуємо пов'язані об'єкти одним запитом
        return qs.select_related('unit').annotate(
            docs_count=Count('documents')  # Припускаємо related_name='documents'
        )
    
    # ✅ Кастомні методи відображення
    @admin.display(description='Статус', ordering='status')
    def colored_status(self, obj):
        """Статус з кольоровим індикатором"""
        colors = {
            OIDStatusChoices.NEW: '#FFA500',  # Помаранчевий
            OIDStatusChoices.ACTIVE: '#28a745',  # Зелений
            OIDStatusChoices.INACTIVE: '#6c757d',  # Сірий
            # Додайте інші статуси
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">⬤ {}</span>',
            color,
            obj.get_status_display()
        )
    
    @admin.display(description='Частина', ordering='unit__code')
    def unit_link(self, obj):
        """Клікабельне посилання на частину"""
        from django.urls import reverse
        from django.utils.safestring import mark_safe
        
        url = reverse('admin:your_app_unit_change', args=[obj.unit.pk])
        return mark_safe(f'<a href="{url}">{obj.unit.code}</a>')
    
    @admin.display(description='Документів', ordering='docs_count')
    def documents_count_display(self, obj):
        """Кількість документів з іконкою"""
        count = getattr(obj, 'docs_count', 0)
        if count > 0:
            return format_html(
                '<span style="background-color: #007bff; color: white; '
                'padding: 2px 6px; border-radius: 3px;">📄 {}</span>',
                count
            )
        return '—'
    
    @admin.display(description='Створено', ordering='created_at')
    def created_at_short(self, obj):
        """Коротке відображення дати"""
        from django.utils import timezone
        if timezone.now().date() == obj.created_at.date():
            return format_html(
                '<span style="color: green;">Сьогодні {}</span>',
                obj.created_at.strftime('%H:%M')
            )
        return obj.created_at.strftime('%d.%m.%Y')
    
    # ✅ Масові дії (actions)
    actions = ['activate_oids', 'deactivate_oids', 'export_to_excel']
    
    @admin.action(description='✅ Активувати вибрані ОІД')
    def activate_oids(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активовано {updated} ОІД')
    
    @admin.action(description='❌ Деактивувати вибрані ОІД')
    def deactivate_oids(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивовано {updated} ОІД', level='warning')
    
    @admin.action(description='📊 Експорт в Excel')
    def export_to_excel(self, request, queryset):
        import openpyxl
        from django.http import HttpResponse
        from openpyxl.utils import get_column_letter
        
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "ОІД"
        
        # Заголовки
        headers = ['Шифр', 'Тип', 'Частина', 'Приміщення', 'Статус', 'Створено']
        ws.append(headers)
        
        # Дані
        for obj in queryset:
            ws.append([
                obj.cipher,
                obj.get_oid_type_display(),
                obj.unit.code,
                obj.room,
                obj.get_status_display(),
                obj.created_at.strftime('%d.%m.%Y')
            ])
        
        # Відповідь
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=oid_export.xlsx'
        wb.save(response)
        return response

# @admin.register(Person)
# class PersonAdmin(SimpleHistoryAdmin):
#     list_display = ('full_name', 'position', 'group', 'is_active')
#     list_filter = ('is_active',)
#     search_fields = ('full_name', 'position')
@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    """Адміністрування виконавців"""
       
    list_display = [
        'full_name', 'position', 'group_badge', 
        'active_tasks_count', 'is_active_badge', 'created_at',
        'group', 'user', 'is_active',
    ]
    list_filter = ['group', 'is_active', 'created_at']
    search_fields = ['full_name', 'user__username', 'surname', 'position']
    list_per_page = 50
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основна інформація', {
            'fields': ('full_name', 'surname', 'position', 'group')
        }),
        ('Обліковий запис', {
            'fields': ('user',)
        }),

        ('Статус', {
            'fields': ('is_active',)
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
            'padding: 3px 10px; border-radius: 12px; font-size: 12px;">{}</span>',
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


@admin.register(WorkRequest)
class WorkRequestAdmin(SimpleHistoryAdmin):
    list_display = ('incoming_number', 'incoming_date', 'unit', 'status', 'created_at')
    list_filter = ('status', 'unit', 'incoming_date')
    search_fields = ('incoming_number', 'unit__code', 'unit__name')
    date_hierarchy = 'incoming_date'


@admin.register(WorkRequestItem)
class WorkRequestItemAdmin(SimpleHistoryAdmin):
    list_display = ('request', 'oid', 'work_type', 'status')
    list_filter = ('work_type', 'status', 'request__unit')
    search_fields = ('oid__cipher', 'request__incoming_number')


@admin.register(DocumentType)
class DocumentTypeAdmin(SimpleHistoryAdmin):
    list_display = ('name', 'oid_type', 'work_type', 'has_expiration', 'duration_months')
    list_filter = ('oid_type', 'work_type', 'has_expiration')
    search_fields = ('name',)


@admin.register(Document)
class DocumentAdmin(SimpleHistoryAdmin):
    list_display = (
        'document_number', 
        'document_type', 
        'oid', 
        'work_date', 
        'doc_process_date', 
        'author', 
        'attestation_registration_sent', # Додано нове поле
        'dsszzi_registered_number',      # Додано нове поле
        'dsszzi_registered_date'       # Додано нове поле
    )
    list_filter = ('document_type', 'work_date', 'author', 'oid__unit', 'attestation_registration_sent')
    search_fields = ('document_number', 'oid__cipher', 'dsszzi_registered_number')
    date_hierarchy = 'doc_process_date'
    # history_list_display = ["document_type", 'work_date', 'author', 'oid__unit' ]


@admin.register(Trip)
class TripAdmin(SimpleHistoryAdmin):
    list_display = ('__str__', 'start_date', 'end_date', 'purpose_short') # Використовуємо __str__ для кращого представлення
    filter_horizontal = ('units', 'oids', 'persons', 'work_requests')
    list_filter = ('start_date', 'units', 'persons')
    search_fields = ('purpose', 'units__code', 'persons__full_name')
    date_hierarchy = 'start_date'

    def purpose_short(self, obj): # Допоміжний метод для короткого опису мети
        if obj.purpose:
            return (obj.purpose[:75] + '...') if len(obj.purpose) > 75 else obj.purpose
        return "-"
    purpose_short.short_description = 'Мета (коротко)'


@admin.register(OIDStatusChange)
class OIDStatusChangeAdmin(SimpleHistoryAdmin):
    list_display = ('oid', 'old_status', 'new_status', 'changed_at', 'changed_by', 'reason_short')
    list_filter = ('old_status', 'new_status', 'changed_at', 'changed_by', 'oid__unit')
    search_fields = ('oid__cipher', 'reason', 'changed_by__full_name')
    date_hierarchy = 'changed_at'

    def reason_short(self, obj): # Короткий опис причини
        if obj.reason:
            return (obj.reason[:75] + '...') if len(obj.reason) > 75 else obj.reason
        return "-"
    reason_short.short_description = 'Причина (коротко)'


@admin.register(AttestationRegistration)
class AttestationRegistrationAdmin(SimpleHistoryAdmin):
    # Оновлюємо поля згідно з новими назвами в моделі AttestationRegistration
    list_display = ('outgoing_letter_number', 'outgoing_letter_date', 'sent_by', 'status', 'created_at')
    list_filter = ('status', 'outgoing_letter_date', 'sent_by')
    search_fields = ('outgoing_letter_number', 'sent_by__full_name', 'units__code')
    filter_horizontal = ('units',)
    date_hierarchy = 'outgoing_letter_date'

@admin.register(AttestationResponse)
class AttestationResponseAdmin(SimpleHistoryAdmin):
    # Оновлюємо поля згідно з новими назвами в моделі AttestationResponse
    list_display = ('attestation_registration_sent', 'response_letter_number', 'response_letter_date', 'received_by', 'created_at')
    list_filter = ('response_letter_date', 'received_by', 'attestation_registration_sent__status')
    search_fields = ('response_letter_number', 'attestation_registration_sent__outgoing_letter_number', 'received_by__full_name')
    date_hierarchy = 'response_letter_date'
    
@admin.register(WorkCompletionRegistration)
class WorkCompletionRegistration(SimpleHistoryAdmin):
    # Оновлюємо поля згідно з новими назвами в моделі WorkCompletionRegistration
    list_display = ('outgoing_letter_number', 'outgoing_letter_date', 'send_by', 'created_at', 'updated_at')
    list_filter = ('outgoing_letter_number', 'outgoing_letter_date', 'send_by', 'created_at', 'updated_at')
    search_fields = ('outgoing_letter_number', 'send_by__full_name', 'units__code')
    date_hierarchy = 'outgoing_letter_date'

@admin.register(WorkCompletionResponse)
class WorkCompletionResponseAdmin(SimpleHistoryAdmin):
    # Оновлюємо поля згідно з новими назвами в моделі WorkCompletionResponse
    list_display = ('registration_request', 'response_letter_number', 'response_letter_date', 'note', 'received_at', 'received_by')
    list_display = ('registration_request', 'response_letter_number', 'response_letter_date', 'received_at', 'received_by')
    list_filter = ('response_letter_date', 'received_at', 'registration_request')
    search_fields = ('response_letter_number', 'registration_request__outgoing_letter_number', 'received_by__full_name')
    date_hierarchy = 'response_letter_date'


@admin.register(TripResultForUnit)
class TripResultForUnitAdmin(SimpleHistoryAdmin):
    list_display = ('outgoing_letter_date', 'trip_info')
    filter_horizontal = ('units', 'oids', 'documents')
    list_filter = ('outgoing_letter_date', 'units')
    search_fields = ('trip__purpose', 'units__code', 'documents__document_number')
    date_hierarchy = 'outgoing_letter_date'

    def trip_info(self, obj):
        return str(obj.trip) if obj.trip else "N/A"
    trip_info.short_description = "Відрядження"


@admin.register(TechnicalTask)
class TechnicalTaskAdmin(SimpleHistoryAdmin):
    list_display = ('oid', 'input_number', 'input_date', 'read_till_date', 'reviewed_by', 'review_result', 'updated_at', 'created_at')
    search_fields = ('input_number', 'oid__cipher', 'reviewed_by__full_name')
    list_filter = ('review_result', 'input_date', 'oid__unit')
    date_hierarchy = 'input_date'

@admin.register(ProcessTemplate)
class ProcessTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'applies_to_oid_type', 'applies_to_pemin_subtype', 'is_active', 'description')

@admin.register(ProcessStep)
class ProcessStepAdmin(admin.ModelAdmin):
    list_display = ('template', 'name', 'order', 'document_type', 'trigger_document_status', 'responsible_party', 'description')

@admin.register(OIDProcess)
class OIDProcessAdmin(admin.ModelAdmin):
    list_display = ('oid', 'template', 'start_date', 'end_date', 'status')
    
@admin.register(OIDProcessStepInstance)
class OIDProcessStepInstanceAdmin(admin.ModelAdmin):
    list_display = ('oid_process', 'process_step', 'status', 'linked_document', 'completed_at')


@admin.register(Declaration)
class DeclarationAdmin(admin.ModelAdmin):
    list_display = ('dsk_eot', 'prepared_number', 'prepared_date', 'registered_number', 'registered_date', 'note', 'created_at', 'updated_at')



@admin.register(DeclarationRegistration)
class DeclarationRegistrationAdmin(admin.ModelAdmin):
    list_display = ('outgoing_letter_number', 'outgoing_letter_date', 'note', 'created_by', 'created_at', 'updated_at', 'response_letter_number', 'response_letter_date', 'response_note', 'response_by', 'response_at')


 