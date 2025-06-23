from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin 
from .models import (
    TerritorialManagement, UnitGroup, Unit, OID,
    Person, WorkRequest, WorkRequestItem,
    DocumentType, Document, Trip, OIDStatusChange,
    AttestationRegistration, AttestationResponse,
    TripResultForUnit, TechnicalTask,
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
    list_display = ('cipher', 'oid_type', 'unit', 'room', 'status', 'created_at') # Додав created_at для інформації
    list_filter = ('oid_type', 'status', 'unit__territorial_management')
    search_fields = ('cipher', 'full_name', 'room')
    date_hierarchy = 'created_at' # Дозволяє навігацію по даті створення
    # history_list_display = ["status"]


@admin.register(Person)
class PersonAdmin(SimpleHistoryAdmin):
    list_display = ('full_name', 'position', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('full_name', 'position')


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
    list_display = ('name', 'oid_type', 'work_type', 'has_expiration', 'duration_months', 'is_required')
    list_filter = ('oid_type', 'work_type', 'has_expiration', 'is_required')
    search_fields = ('name',)


@admin.register(Document)
class DocumentAdmin(SimpleHistoryAdmin):
    list_display = (
        'document_number', 
        'document_type', 
        'oid', 
        'work_date', 
        'process_date', 
        'author', 
        'attestation_registration_sent', # Додано нове поле
        'dsszzi_registered_number',      # Додано нове поле
        'dsszzi_registered_date'       # Додано нове поле
    )
    list_filter = ('document_type', 'work_date', 'author', 'oid__unit', 'attestation_registration_sent')
    search_fields = ('document_number', 'oid__cipher', 'dsszzi_registered_number')
    date_hierarchy = 'process_date'
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
    
	 