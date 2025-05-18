# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('documents/create/', views.document_create, name='document_create'),
    path('documents/request/', views.document_request, name='document_request'),
    path('ajax/load-oids/', views.load_oids, name='ajax_load_oids'),
    path('ajax/get-oids/', views.get_oids_by_unit, name='get_oids_by_unit'),
]
