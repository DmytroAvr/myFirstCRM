from django.contrib import admin
from .models import ManagementUnit, MBase, OID, Document, WorkHistory, Trip, Personnel

@admin.register(ManagementUnit)
class ManagementUnitAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(MBase)
class MBaseAdmin(admin.ModelAdmin):
    list_display = ('name', 'management_unit')
    list_filter = ('management_unit',)

@admin.register(OID)
class OIDAdmin(admin.ModelAdmin):
    list_display = ('name', 'MBase', 'status', 'OID_type')
    list_filter = ('MBase', 'status', 'OID_type')

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('oid', 'name', 'expiration_date')
    list_filter = ('expiration_date',)

@admin.register(WorkHistory)
class WorkAdmin(admin.ModelAdmin):
    list_display = ('oid', 'description', 'date')
    list_filter = ('date',)

@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('oid', 'date')
    list_filter = ('date',)

@admin.register(Personnel)
class PersonAdmin(admin.ModelAdmin):
    list_display = ('full_name',)
