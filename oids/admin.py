from django.contrib import admin
# from django_admin_multi_select_filter.filters import MultiSelectFieldListFilter

# %%%%%ооо111111
# from .forms import DocumentForm
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
    list_display = ('Unit', 'work_type', 'incoming_number', 'incoming_date', 'status')
   
    list_filter = ('Unit', 'work_type', 'status')

@admin.register(Trip)
class WorkRequestAdmin(admin.ModelAdmin):
    list_filter = (
        ('start_date', admin.DateFieldListFilter),
    )

@admin.register(DocumentType)
class DocumentType(admin.ModelAdmin):
    list_display = ('oid_type', 'work_type', 'name', 'valid_days')


@admin.register(Document)
class Document(admin.ModelAdmin):
    list_display = ('unit', 'oid', 'work_date', 'work_type', 'document_type', 'document_number', 'process_date')

    admin.site.register(Person)
