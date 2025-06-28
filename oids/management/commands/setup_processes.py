# oids/management/commands/setup_processes.py

from django.core.management.base import BaseCommand
from django.db import transaction
from oids.models import (
    DocumentType, ProcessTemplate, ProcessStep,
    DocumentProcessingStatusChoices, OIDTypeChoices, PeminSubTypeChoices
)

class Command(BaseCommand):
    help = 'Створює початкові шаблони процесів та типи документів'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Налаштування початкових процесів...")

        # --- 1. Створення необхідного типу документа ---
        self.stdout.write("Створення типу документа 'Декларація відповідності'...")
        doc_type, _ = DocumentType.objects.get_or_create(
            name="Декларація відповідності",
            oid_type='СПІЛЬНИЙ', # Спільний, бо може стосуватись різних підтипів
            work_type='СПІЛЬНИЙ',
            defaults={
                'has_expiration': False,
                'duration_months': 0
            }
        )

        # --- 2. Створення шаблону процесу "ДСК-Декларація" ---
        self.stdout.write("Створення шаблону процесу 'ДСК-Декларація'...")
        template, created = ProcessTemplate.objects.get_or_create(
            name="ДСК-Декларація",
            defaults={
                'applies_to_oid_type': OIDTypeChoices.PEMIN,
                'applies_to_pemin_subtype': [PeminSubTypeChoices.AS1_4_DSK, PeminSubTypeChoices.AS23_4_DSK],
                'is_active': True,
                'description': 'Процес створення ОІД та реєстрації Декларації відповідності для АС ДСК.'
            }
        )

        if not created:
            # Якщо шаблон вже існує, видаляємо старі кроки, щоб уникнути дублікатів
            template.steps.all().delete()
            self.stdout.write(self.style.WARNING("Існуючий шаблон знайдено, старі кроки видалено."))
        
        # --- 3. Створення кроків для шаблону ---
        self.stdout.write("Створення кроків для шаблону...")
        ProcessStep.objects.create(
            template=template,
            name="Відправка декларації на реєстрацію в ДССЗЗІ",
            order=10,
            document_type=doc_type,
            trigger_document_status=DocumentProcessingStatusChoices.SENT_FOR_REGISTRATION,
            responsible_party=ProcessStep.ResponsiblePartyChoices.GU,
            # description="Створити ОІД та Декларацію, відправити до ДССЗЗІ."
            description="Відправити пакет з декларацій надісланих від вч на реєстрацію до ДССЗЗІ (цей крок також має: 1. Створювати ОІД відповідно характеристикам. 2  додавати до відповідного ОІД документ Декларація відповідності) ОІД= Військова частина: вказати (відповідно таблиці). . Тип ОІД: ПЕМІН (авточатично). Шифр ОІД: вказати (відповідно таблиці)(default: ДСКДекларація АС1/2/3).. Гриф:ДСК (авточатично). Повна назва ОІД: вказати (відповідно таблиці)(необовязково).. Приміщення №:ДСК (авточатично). Поточний стан ОІД:Отримано Декларацію (авточатично). Примітка: вказати (відповідно таблиці)(необовязково).. Тип ЕОТ:  вказати (відповідно таблиці).(доступні варіанти АС1_4ДСК або АС2/3-4 ДСК).. Серійний номер: вказати (відповідно таблиці)(необовязково).. Інвентарний номер: вказати (відповідно таблиці)(необовязково)."
        )

        ProcessStep.objects.create(
            template=template,
            name="Відправка реєстраційних номерів до в/ч",
            order=20,
            document_type=doc_type,
            trigger_document_status=DocumentProcessingStatusChoices.COMPLETED,
            responsible_party=ProcessStep.ResponsiblePartyChoices.GU,
            # description="Внести реєстраційні дані та змінити статус ОІД на Активний."
            description="Відправити пакет з декларацій зареєстрованих в  ДССЗЗІ до вч (цей крок також має: 1. змінити статус ОІД в таблиці на Активний. 2  додавати до відповідного документу Декларація відповідності реєстраційний номер та дату реєстрації)"
        )

        self.stdout.write(self.style.SUCCESS("Налаштування процесів успішно завершено!"))