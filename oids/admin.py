from django.contrib import admin
from .models import (
    TerritorialManagement, UnitGroup, Unit, OID,
    Person, WorkRequest, WorkRequestItem,
    DocumentType, Document,
    Trip, OIDStatusChange,
    AttestationRegistration, AttestationItem, AttestationResponse,
    TripResultForUnit, TechnicalTask
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
class UnitAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'city', 'territorial_management')
    search_fields = ('code', 'name', 'city')
    list_filter = ('territorial_management', 'unit_groups')


@admin.register(OID)
class OIDAdmin(admin.ModelAdmin):
    list_display = ('cipher', 'oid_type', 'unit', 'room', 'status')
    list_filter = ('oid_type', 'status', 'unit__territorial_management')
    search_fields = ('cipher', 'full_name', 'room')


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'position', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('full_name', 'position')


@admin.register(WorkRequest)
class WorkRequestAdmin(admin.ModelAdmin):
    list_display = ('incoming_number', 'unit', 'status')
    list_filter = ('status', 'unit')
    search_fields = ('incoming_number',)


@admin.register(WorkRequestItem)
class WorkRequestItemAdmin(admin.ModelAdmin):
    list_display = ('request', 'oid', 'work_type', 'status')
    list_filter = ('work_type', 'status')
    search_fields = ('oid__cipher',)


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'oid_type', 'work_type', 'has_expiration', 'duration_months', 'is_required')
    list_filter = ('oid_type', 'work_type', 'has_expiration', 'is_required')
    search_fields = ('name',)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('document_type', 'document_number', 'oid', 'work_date', 'process_date', 'author')
    list_filter = ('document_type', 'work_date', 'author')
    search_fields = ('document_number', 'oid__cipher')


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'end_date', 'purpose')
    filter_horizontal = ('units', 'oids', 'persons', 'work_requests')


@admin.register(OIDStatusChange)
class OIDStatusChangeAdmin(admin.ModelAdmin):
    list_display = ('oid', 'old_status', 'new_status', 'changed_at', 'changed_by')
    list_filter = ('old_status', 'new_status')
    search_fields = ('oid__cipher',)


@admin.register(AttestationRegistration)
class AttestationRegistrationAdmin(admin.ModelAdmin):
    list_display = ('process_date', 'registration_number')
    filter_horizontal = ('units',)
    search_fields = ('registration_number',)


@admin.register(AttestationItem)
class AttestationItemAdmin(admin.ModelAdmin):
    list_display = ('registration', 'oid', 'document')
    search_fields = ('oid__cipher', 'document__document_number')


@admin.register(AttestationResponse)
class AttestationResponseAdmin(admin.ModelAdmin):
    list_display = ('registration', 'registered_number', 'registered_date', 'recorded_date')


@admin.register(TripResultForUnit)
class TripResultForUnitAdmin(admin.ModelAdmin):
    list_display = ('process_date', 'trip')
    filter_horizontal = ('units', 'oids', 'documents')


@admin.register(TechnicalTask)
class TechnicalTaskAdmin(admin.ModelAdmin):
    list_display = ('input_number', 'input_date', 'oid', 'review_result', 'reviewed_by')
    search_fields = ('input_number', 'oid__cipher')
    list_filter = ('review_result',)
