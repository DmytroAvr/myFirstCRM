from django.contrib import admin
from .models import Unit, OID, Document, Trip, Person, WorkRequest, DocumentType, AttestationItem,  AttestationRegistration, TripResultForUnit, TechnicalTask 
from .forms import TripResultForUnitForm



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



#  нові частини 

class AttestationItemInline(admin.TabularInline):
    model = AttestationItem
    extra = 1

@admin.register(AttestationRegistration)
class AttestationRegistrationAdmin(admin.ModelAdmin):
    inlines = [AttestationItemInline]
    list_display = ("process_date", "get_units", "note")
    filter_horizontal = ("units",)

    def get_units(self, obj):
        return ", ".join([str(u) for u in obj.units.all()])
    get_units.short_description = "Військові частини"

    from django.contrib import admin

@admin.register(TripResultForUnit)
class TripResultForUnitAdmin(admin.ModelAdmin):
    form = TripResultForUnitForm
    list_display = ("process_date", "get_units", "get_oids", "get_documents_count")
    filter_horizontal = ("units", "oids", "documents")

    def get_units(self, obj):
        return ", ".join([str(u) for u in obj.units.all()])
    get_units.short_description = "Частини"

    def get_oids(self, obj):
        return ", ".join([str(o) for o in obj.oids.all()])
    get_oids.short_description = "ОІД"

    def get_documents_count(self, obj):
        return obj.documents.count()
    get_documents_count.short_description = "К-сть документів"

# Технічне завдання
@admin.register(TechnicalTask) 
class TechnicalTaskAdmin(admin.ModelAdmin):
    list_display = ('input_number', 'input_date', 'oid', 'reviewed_by', 'review_result')
    list_filter = ('review_result', 'input_date')
    search_fields = ('input_number', 'reviewed_by', 'oid__name')

