# oids/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_dashboard, name='main_dashboard'),
    path('oid/<int:oid_id>/', views.oid_detail_view, name='oid_detail'),
    
    # URLs для AJAX запитів
    path('ajax/load-oids-for-unit/', views.ajax_load_oids_for_unit, name='ajax_load_oids_for_unit'),
    # Додай інші AJAX URL-и, якщо вони потрібні з твого filtering_dynamic.js
    
    # URLs для форм (заглушки)
    # path('request/add/', views.add_work_request_view, name='add_work_request_view_name'),
    # path('trip/plan/', views.plan_trip_view, name='plan_trip_view_name'),
    # path('document/process/', views.add_document_processing_view, name='add_document_processing_view_name'),

     # URL-и для форм
    path('request/add/', views.add_work_request, name='add_work_request'),
    path('trip/plan/', views.plan_trip, name='plan_trip'),
    path('document/process/', views.add_document_processing, name='add_document_processing'),

]