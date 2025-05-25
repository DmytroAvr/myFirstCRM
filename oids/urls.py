# oids/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_dashboard, name='main_dashboard'),
    path('oid/<int:oid_id>/', views.oid_detail_view, name='oid_detail'),
    
    # URL-и для форм
    path('request/add/', views.add_work_request, name='add_work_request'),
    path('trip/plan/', views.plan_trip, name='plan_trip'),
    path('document/process/', views.add_document_processing, name='add_document_processing'),
]