# oids/apps.py
from django.apps import AppConfig

class OidsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'oids'

    def ready(self):
        import oids.signals # Імпортуємо наш файл з сигналами
        