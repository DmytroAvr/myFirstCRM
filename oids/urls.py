# D:\myFirstCRM\oids\urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('ajax/load-oids/', views.load_oids, name='ajax_load_oids'),
    path('ajax/get-oids/', views.get_oids_by_unit, name='get_oids_by_unit'),
    path('ajax/create/', views.create_oid_ajax, name='create_oid_ajax'),
    path('ajax/load-oids-for-units/', views.load_oids_for_units, name='ajax_load_oids_for_units'),
    path('ajax/load-oids-for-unit/', views.load_oids_for_unit, name='ajax_load_oids_for_unit'),
    path('ajax/load-documents-for-oids/', views.load_documents_for_oids, name='ajax_load_documents_for_oids'),


    path('documents/create/', views.document_create, name='document_create'),
    path('documents/request/', views.document_request, name='document_request'),
    # D:\myFirstCRM\oids\urls.py
    path('attestation/new/', views.create_attestation_registration, name='attestation_new'),
    path('trip_result/new/', views.create_trip_result, name='trip_result_new'),
    path('technical_tasks/create/', views.technical_task_create, name='technical_task_create'),
    # path('trip_result/list/', views.trip_result_list, name='trip_result_list'),
    path('oids/create/', views.create_oid, name='oid_create')

]
