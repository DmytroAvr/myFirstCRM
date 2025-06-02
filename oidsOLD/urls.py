# D:\myFirstCRM\oids\urls.py
from django.urls import path, include
from . import views


urlpatterns = [
    path('ajax/load-oids/', views.load_oids, name='ajax_load_oids'),
    path('ajax/get-oids/', views.get_oids_by_unit, name='get_oids_by_unit'),
    path('ajax/create/', views.create_oid_ajax, name='create_oid_ajax'),
    path('ajax/load-documents-for-oids/', views.load_documents_for_oids, name='ajax_load_documents_for_oids'),
    path('ajax/get-oid-status/', views.get_oid_status, name='ajax_get_oid_status'),

    path('ajax/get-work-request-details/', views.get_work_request_details, name='get_work_request_details'),
    path('ajax/load-technical-tasks-for-oid/', views.load_technical_tasks_for_oid, name='load_technical_tasks_for_oid'),


    path('ajax/load-oids-for-units/', views.load_oids_for_units, name='ajax_load_oids_for_units'),
    path('ajax/load-oids-for-unit/', views.load_oids_for_unit, name='ajax_load_oids_for_unit'),

    path('ajax/get-requests-by-oid/', views.get_requests_by_oid, name='get_requests_by_oid'),
    path('ajax/get-requests-by-oids/', views.get_requests_by_oids, name='get_requests_by_oids'),

    # path('api/oids/', views.get_oids_by_unit, name='get_oids_by_unit'),
    # path('api/requests/', views.get_requests_by_oid, name='get_requests_by_oid'),
    
    path('api/oids/', views.get_oids_by_units, name='get_oids_by_units'),
    path('api/requests/', views.get_requests_by_oids, name='get_requests_by_oids'),

    path('documents/done/', views.document_done, name='document_done'),


    path('work/request/', views.work_request, name='work_request'),

	path('technical-task/create/', views.technical_task_create_view, name='technical_task_create'),
	path('technical-task/process/', views.technical_task_process_view, name='technical_task_process_select'), # Для вибору ТЗ на формі
	path('technical-task/<int:task_id>/process/', views.technical_task_process_view, name='technical_task_process_specific'), # Для опрацювання конкретного ТЗ


    path('trip_create/', views.trip_create_view, name='trip-create'),

    path('technical_tasks/create/', views.technical_task_create, name='technical_task_create'),
    path('technical_tasks_list/', views.technical_task_list, name='technical_task_list'),

    # path('oids/create/', веде до посилання http://127.0.0.1:8000/oids/oids/oid_******
    path('create/', views.create_oid, name='oid_create'),
    path('status-change/', views.change_oid_status, name='oid_status_change'),

    path('send_doc/cip', views.send_doc_cip, name='send_doc_cip'),
    path('send_doc/unit/', views.send_doc_unit, name='send_doc_unit'),


    path('<int:oid_id>/', views.oid_details, name='oid_details'),
    path('unit_overview/', views.unit_overview, name='unit_overview'),
    path('work_requests/', views.work_request_list, name='work_request_list'),
    path('trip_list/', views.trip_list, name='trip-list'),
]
