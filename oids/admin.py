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
    list_display = ('name', 'Unit', 'status')
    list_filter = ('Unit', 'status', 'oid_type')

@admin.register(WorkRequest)
class WorkRequestAdmin(admin.ModelAdmin):
    list_display = ('Unit', 'work_type', 'incoming_number', 'incoming_date', 'status')
   
    list_filter = ('Unit', 'work_type', 'status')

@admin.register(Trip)
class WorkRequestAdmin(admin.ModelAdmin):
    # list_display = ('__str__', 'start_date', 'end_date')
    list_filter = (
        ('start_date', admin.DateFieldListFilter),
    )


@admin.register(DocumentType)
class DocumentType(admin.ModelAdmin):
    list_display = ('oid_type', 'work_type', 'name', 'valid_days')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
#     form = DocumentForm

# %%%%%ооо111111
# class DocumentAdmin(admin.ModelAdmin):
#     form = DocumentForm
# class Media:
#     js = ('admin/js/jquery.init.js', 'js/filter_document_type.js',)
    


    admin.site.register(Person)


# admin.site.register(DocumentType)
# admin.site.register()



    # list_filter = (
    #     # … інші фільтри …,
    #     ('work_type', MultiSelectFieldListFilter),  # фільтр для MultiSelectField
    # )