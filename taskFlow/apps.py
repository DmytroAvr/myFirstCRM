from django.apps import AppConfig

class TaskFlowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'taskFlow'
    verbose_name = 'Управління завданнями'
    
    def ready(self):
        """Імпорт сигналів при ініціалізації застосунку"""
        import taskFlow.signals