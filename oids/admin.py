from django.contrib import admin
from .models import Unit, OID, Document, Trip, Person, WorkRequest, DocumentType

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'management_unit', 'city', 'directionGroup')
    list_filter = ('management_unit', 'city',)

@admin.register(OID)
class OIDAdmin(admin.ModelAdmin):
    list_display = ('name', 'unit', 'status')
    list_filter = ('unit', 'status', 'oid_type')

@admin.register(WorkRequest)
class WorkRequestAdmin(admin.ModelAdmin):
    list_display = ('unit', 'get_work_types', 'get_oids', 'incoming_number', 'incoming_date', 'status')
    list_filter = ('unit', 'items__work_type', 'items__oid', 'status')

    @admin.display(description='Типи робіт')
    def get_work_types(self, obj):
        work_types = obj.items.values_list('work_type', flat=True).distinct()
        return ", ".join(work_types)

    @admin.display(description='ОІД')
    def get_oids(self, obj):
        oids = obj.items.values_list('oid__name', flat=True).distinct()
        return ", ".join(oids)

@admin.register(Trip)
class WorkRequestAdmin(admin.ModelAdmin):
    list_filter = (
        ('start_date', admin.DateFieldListFilter),
    )

# @admin.register(DocumentType)
# class DocumentType(admin.ModelAdmin):
#     list_display = ('oid_type', 'work_type', 'name', 'valid_days')


@admin.register(Document)
class Document(admin.ModelAdmin):
    list_display = ('unit', 'oid', 'work_date', 'work_type', 'document_type', 'document_number', 'process_date', 'author')
    list_filter = ('unit', 'oid', 'work_date', 'work_type', 'process_date', 'author')

    admin.site.register(Person)
