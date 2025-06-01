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
    path('ajax/load-oids-for-multiple-units/', views.ajax_load_oids_for_multiple_units, name='ajax_load_oids_for_multiple_units'), # Новий URL
    path('ajax/load-work-requests-for-oids/', views.ajax_load_work_requests_for_oids, name='ajax_load_work_requests_for_oids'),
	path('ajax/load-work-request-items-for-oid/', views.ajax_load_work_request_items_for_oid, name='ajax_load_work_request_items_for_oid'),
	path('ajax/load-document-types-for-oid-and-work/', views.ajax_load_document_types_for_oid_and_work, name='ajax_load_document_types_for_oid_and_work'),
	path('ajax/get-oid-current-status/', views.ajax_get_oid_current_status, name='ajax_get_oid_current_status'),
	path('ajax/load-attestation-acts-for-oid/', views.ajax_load_attestation_acts_for_oid, name='ajax_load_attestation_acts_for_oid'),
	path('ajax/load-attestation-acts-for-multiple-oids/', views.ajax_load_attestation_acts_for_multiple_oids, name='ajax_load_attestation_acts_for_multiple_oids'),
	path('ajax/load-units-for-trip/', views.ajax_load_units_for_trip, name='ajax_load_units_for_trip'),
	path('ajax/load-oids-for-trip-inits/', views.ajax_load_oids_for_trip_units, name='ajax_load_oids_for_trip_units'),
	path('ajax/load-documents-for-trip-oids/', views.ajax_load_documents_for_trip_oids, name='ajax_load_documents_for_trip_oids'),

	# 
	# 
	# 

    # URLs для форм
    path('trip/plan/', views.plan_trip_view, name='plan_trip_view_name'),
    path('document/add/', views.add_document_processing_view, name='add_document_processing_view_name'),
    path('trip/result/', views.send_trip_results_view, name='send_trip_results_form'),
    # Якщо форма додавання документа викликається з контексту ОІД:
    path('oid/<int:oid_id>/document/add/', views.add_document_processing_view, name='add_document_for_oid_view_name'),
    path('ajax/oid/create/', views.ajax_create_oid_view, name='ajax_create_oid'),
	# Якщо форма додавання документа викликається з контексту елемента заявки:
    path('work-request-item/<int:work_request_item_id>/document/add/', views.add_document_processing_view, name='add_document_for_work_request_item_view_name'),
    path('request/add/', views.add_work_request_view, name='add_work_request_view_name'),
	# Отримати Status OID
	path('oid/update-status/', views.update_oid_status_view, name='update_oid_status'),
	path('oid/<int:oid_id_from_url>/update-status/', views.update_oid_status_view, name='update_specific_oid_status'),


    
    
    path('attestation-registration/send/', views.send_attestation_for_registration_view, name='send_attestation_for_registration'), # URL для форми створення нової відправки на реєстрацію
    path('attestation-response/record/', views.record_attestation_response_view, name='record_attestation_response'), # URL для форми внесення відповіді ДССЗЗІ
    path('attestation-registration/<int:att_reg_sent_id>/record-response/', views.record_attestation_response_view, name='record_attestation_response_for_registration'), # передавати ID відправки в URL для форми відповіді

    


 

	path('summary-hub/', views.summary_information_hub_view, name='summary_information_hub'),
    # Далі будемо додавати URL-и для кожного списку моделей
    path('documents/', views.document_list_view, name='list_documents'),
    path('units/', views.unit_list_view, name='list_units'),

    # Наприклад, для Територіальних управлінь:
    path('territorial-managements/', views.territorial_management_list_view, name='list_territorial_managements'),
    # І так далі для:
    path('unit-groups/', views.unit_group_list_view, name='list_unit_groups'),
    path('document-types/', views.document_type_list_view, name='list_document_types'),
    path('persons/', views.person_list_view, name='list_persons'),
    path('units/', views.unit_list_view, name='list_units'),
    path('oids-list/', views.oid_list_view, name='list_oids'), # назва oids_list_view щоб не плутати з oid_detail_view
    path('work-requests/', views.work_request_list_view, name='list_work_requests'),
    path('trips/', views.trip_list_view, name='list_trips'),
    path('technical-tasks/', views.technical_task_list_view, name='list_technical_tasks'),
    path('attestation-registrations/', views.attestation_registration_list_view, name='list_attestation_registrations'),
    path('attestation-responses/', views.attestation_response_list_view, name='list_attestation_responses'),
    path('trip-results/', views.trip_result_for_unit_list_view, name='list_trip_results_for_units'),
    path('oid-status-changes/', views.oid_status_change_list_view, name='list_oid_status_changes'),
   	path('attestation-registrations/', views.attestation_registration_list_view, name='list_attestation_registrations'), # URL для списку Відправок на реєстрацію
    path('attestation-responses/', views.attestation_response_list_view, name='list_attestation_responses'),  # URL для списку Отриманих відповідей на реєстрацію

	# path("person-autocomplete/", PersonAutocompleteView.as_view(), name="person_autocomplete"),

]