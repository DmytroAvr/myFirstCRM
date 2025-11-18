"""
URL Configuration для TaskFlow
"""

from django.urls import path
from . import views

app_name = 'taskFlow'

urlpatterns = [
    # Список проєктів
    path('', views.project_list, name='project_list'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/board/', views.project_board, name='project_board'),
    
    # Завдання
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/<int:pk>/', views.task_detail, name='task_detail'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/<int:pk>/edit/', views.task_edit, name='task_edit'),
    path('tasks/<int:pk>/delete/', views.task_delete, name='task_delete'),
    
    # API endpoints (якщо потрібно)
    path('api/tasks/<int:pk>/status/', views.task_update_status, name='task_update_status'),
    path('api/tasks/<int:pk>/assign/', views.task_assign, name='task_assign'),
]