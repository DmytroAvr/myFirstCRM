# :\myFirstCRM\oids\urls.py
from django.urls import path
from . import views

app_name = 'oids' # Важливо для {% url 'oids:view_name' %}

urlpatterns = [
    path('', views.main_dashboard, name='main_dashboard'),
    path('oid/<int:oid_id>/', views.oid_detail_view, name='oid_detail_view_name'), # Дай осмислене ім'я
    
    # AJAX URLs
    path('ajax/load-oids-for-unit/', views.ajax_load_oids_for_unit, name='ajax_load_oids_for_unit'),
    path('ajax/load-oids-categorized/', views.ajax_load_oids_for_unit_categorized, name='ajax_load_oids_categorized'), # Новий URL
    
    # URLs для форм
    path('trip/plan/', views.plan_trip_view, name='plan_trip_view_name'),
    path('document/add/', views.add_document_processing_view, name='add_document_processing_view_name'),
    # Якщо форма додавання документа викликається з контексту ОІД:
    path('oid/<int:oid_id>/document/add/', views.add_document_processing_view, name='add_document_for_oid_view_name'),
    # Якщо форма додавання документа викликається з контексту елемента заявки:
    path('work-request-item/<int:work_request_item_id>/document/add/', views.add_document_processing_view, name='add_document_for_work_request_item_view_name'),
    path('request/add/', views.add_work_request_view, name='add_work_request_view_name'),
]