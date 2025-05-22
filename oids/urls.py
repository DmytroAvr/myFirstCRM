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
    path('ajax/get-oid-status/', views.get_oid_status, name='ajax_get_oid_status'),

    path('documents/done/', views.document_done, name='document_done'),


    path('work/request/', views.work_request, name='work_request'),
    path('work_requests/', views.work_request_list, name='work_request_list'),


    path('attestation/new/', views.create_attestation_registration, name='attestation_new'),

    path('trip_create/', views.trip_create_view, name='trip-create'),
    path('trip_list/', views.trip_list, name='trip-list'),

    path('trip_result/new/', views.create_trip_result, name='trip_result_new'),
    path('technical_tasks/create/', views.technical_task_create, name='technical_task_create'),
    path('technical_tasks_list/', views.technical_task_list, name='technical_task_list'),

    path('oids/create/', views.create_oid, name='oid_create'),
    path('oids/status-change/', views.change_oid_status, name='oid_status_change'),
]
