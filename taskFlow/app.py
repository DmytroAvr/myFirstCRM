from django.apps import AppConfig

class taskFlowConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'taskFlow'
    
    def ready(self):
        import taskFlow.signals  # Імпортуємо сигнали