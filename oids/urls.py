# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('documents/create/', views.document_create, name='document_create'),
    path('ajax/load-oids/', views.load_oids, name='ajax_load_oids'),
]
