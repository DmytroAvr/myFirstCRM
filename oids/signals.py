# oids/signals.py
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver
from django.utils import timezone
import datetime 
from .models import (Trip, WorkRequestItem, WorkTypeChoices, OID, add_working_days,
                     Document, OIDProcessStepInstance, ProcessStepStatusChoices, 
                     OIDStatusChoices )

# Переконайтесь, що функція add_working_days визначена коректно
# (як ми обговорювали, щоб вона додавала N робочих днів ПІСЛЯ start_date)

@receiver(m2m_changed, sender=Trip.work_requests.through)
@receiver(m2m_changed, sender=Trip.oids.through) # Слухаємо зміни на обох M2M полях
def calculate_doc_processing_deadlines_on_trip_change(sender, instance, action, pk_set, **kwargs):
    """
    Розраховує та встановлює doc_processing_deadline для WorkRequestItems,
    коли змінюються M2M зв'язки work_requests або oids для Trip, 
    АБО коли Trip оновлюється і має end_date (це обробляється окремо, якщо потрібно).
    Цей сигнал спрацьовує ПІСЛЯ того, як M2M зв'язки були фактично змінені в базі.
    """
    if action == "post_add" or action == "post_remove" or action == "post_clear":
        trip = instance # instance тут - це екземпляр Trip
        
        # Також можна додати перевірку, чи змінився сам Trip.end_date,
        # але m2m_changed не дає інформації про зміни інших полів Trip.
        # Для цього краще використовувати post_save сигнал для Trip.

        print(f"SIGNAL (m2m_changed for Trip): Triggered for Trip ID {trip.pk}, action: {action}, pk_set: {pk_set}")

        if trip.end_date:
            print(f"SIGNAL: Trip ID {trip.pk} has end_date: {trip.end_date}. Proceeding with deadline calculation.")
            
            linked_work_requests = trip.work_requests.all()
            linked_oids_direct = trip.oids.all() # ОІДи, які явно додані до відрядження

            if not linked_work_requests.exists():
                print(f"SIGNAL: Trip {trip.pk} has no linked WorkRequests. No item deadlines to update based on WRs.")
                return # Виходимо, якщо немає пов'язаних заявок
            
            if not linked_oids_direct.exists():
                print(f"SIGNAL: Trip {trip.pk} has no OIDs directly linked. No items to process if filter requires direct OID link.")
                # Залежно від вашої логіки, можливо, тут теж варто вийти,
                # або змінити фільтр нижче, щоб брати ОІДи тільки з WorkRequestItems.
                # Поточна логіка вимагає, щоб ОІД був і в заявці, і у відрядженні.

            # Знаходимо WorkRequestItems, які належать до Заявок з цього відрядження
            # І стосуються ОІДів, які також є у цьому відрядженні.
            items_to_process = WorkRequestItem.objects.filter(
                request__in=linked_work_requests,
                oid__in=linked_oids_direct 
                # Можна додати: doc_processing_deadline__isnull=True, якщо оновлювати тільки раз
            ).select_related('oid', 'request__unit')

            print(f"SIGNAL: Found {items_to_process.count()} WorkRequestItems for Trip {trip.pk} to update/check deadline.")
            
            start_counting_from_date = trip.end_date 

            for item in items_to_process:
                print(f"SIGNAL: Processing WRI ID {item.id} (OID: {item.oid.cipher}, WorkType: {item.work_type})")
                days_for_processing = 0
                if item.work_type == WorkTypeChoices.IK:
                    days_for_processing = 10
                elif item.work_type == WorkTypeChoices.ATTESTATION:
                    days_for_processing = 15
                
                if days_for_processing > 0:
                    # add_working_days(start_date, N) має повернути N-й робочий день ПІСЛЯ start_date
                    new_deadline = add_working_days(start_counting_from_date, days_for_processing)
                    
                    if item.doc_processing_deadline != new_deadline:
                        item.doc_processing_deadline = new_deadline
                        item.save(update_fields=['doc_processing_deadline', 'updated_at'])
                        print(f"SIGNAL: For WRI ID {item.id} -> Deadline SET/UPDATED to: {item.doc_processing_deadline}")
                    else:
                        print(f"SIGNAL: For WRI ID {item.id} -> Deadline {item.doc_processing_deadline} (no change needed).")
                else:
                    # Якщо тип робіт не передбачає дедлайну, можна очистити поле
                    if item.doc_processing_deadline is not None:
                        item.doc_processing_deadline = None
                        item.save(update_fields=['doc_processing_deadline', 'updated_at'])
                        print(f"SIGNAL: For WRI ID {item.id} (Type: {item.work_type}) -> Deadline CLEARED.")
        else:
            print(f"SIGNAL: Trip ID {trip.pk} has no end_date. Deadlines not calculated by m2m_changed signal.")

# Додатково, якщо ви хочете оновлювати дедлайни при зміні Trip.end_date (навіть якщо M2M не змінились):

@receiver(post_save, sender=Trip)
def update_deadlines_on_trip_save(sender, instance, created, update_fields, **kwargs):
    # 'update_fields' доступний тільки якщо save() викликається з update_fields
    # Якщо його немає, то ми не знаємо, чи змінилася end_date, тому перераховуємо завжди, коли вона є.
    # Або можна порівнювати з попереднім значенням, як у вашому save() методі.
    
    trip = instance
    recalculate = False
    if created and trip.end_date: # Новий тріп з датою завершення
        recalculate = True
        print(f"SIGNAL (post_save for Trip): New Trip ID {trip.pk} with end_date. Flagging for deadline recalc.")
    elif not created and trip.end_date:
        # Перевіряємо, чи змінилася end_date (якщо update_fields передано)
        if update_fields and 'end_date' in update_fields:
            recalculate = True
            print(f"SIGNAL (post_save for Trip): Trip ID {trip.pk} end_date was updated. Flagging for deadline recalc.")
        elif not update_fields: # Якщо update_fields не передано, важко сказати, чи end_date змінилась. Перерахуємо про всяк випадок.
            # Тут можна додати логіку порівняння з попереднім значенням, якщо це критично
            # Для простоти, якщо end_date є, і це оновлення, можна спробувати перерахувати.
            # Але це може викликати зайві перерахунки, якщо M2M теж змінюються.
            # Краще покладатися на m2m_changed для M2M, а тут - тільки якщо сама end_date змінилася.
            # Для цього потрібно зберігати old_end_date, як ви робили в save().
            # Або просто викликати логіку, якщо end_date є.
            # Поки що цей сигнал буде реагувати тільки на створення з end_date або явне оновлення end_date.
            pass # Уникаємо подвійного спрацювання, якщо m2m_changed вже все зробив.
                 # Якщо потрібно реагувати на зміну ТІЛЬКИ end_date, тут потрібна логіка з old_end_date.

    if recalculate:
        # Викликаємо ту саму логіку, що й у m2m_changed сигналі
        # Щоб уникнути дублювання, можна винести логіку в окрему функцію
        _calculate_and_set_deadlines_for_trip(trip)


def _calculate_and_set_deadlines_for_trip(trip_instance):
    """Допоміжна функція для розрахунку дедлайнів."""
    if not trip_instance.end_date:
        print(f"HELPER_DEADLINE: Trip ID {trip_instance.pk} has no end_date. Skipping.")
        return

    print(f"HELPER_DEADLINE: Calculating for Trip ID {trip_instance.pk}, End Date: {trip_instance.end_date}.")
    linked_work_requests = trip_instance.work_requests.all()
    linked_oids_direct = trip_instance.oids.all()

    if not linked_work_requests.exists() or not linked_oids_direct.exists():
        print(f"HELPER_DEADLINE: Trip {trip_instance.pk} missing linked WRs or OIDs. Skipping.")
        return

    items_to_process = WorkRequestItem.objects.filter(
        request__in=linked_work_requests,
        oid__in=linked_oids_direct
    ).select_related('oid')
    
    print(f"HELPER_DEADLINE: Found {items_to_process.count()} WRI for Trip {trip_instance.pk}.")
    start_counting_from_date = trip_instance.end_date

    for item in items_to_process:
        days = 10 if item.work_type == WorkTypeChoices.IK else (15 if item.work_type == WorkTypeChoices.ATTESTATION else 0)
        if days > 0:
            new_deadline = add_working_days(start_counting_from_date, days)
            if item.doc_processing_deadline != new_deadline:
                item.doc_processing_deadline = new_deadline
                item.save(update_fields=['doc_processing_deadline', 'updated_at'])
                print(f"HELPER_DEADLINE: WRI ID {item.id} (OID: {item.oid.cipher}) deadline -> {new_deadline}")
                

@receiver(post_save, sender=Document)
def update_process_step_on_document_change(sender, instance, created, **kwargs):
    """
    Оновлює статус кроку процесу, коли змінюється статус пов'язаного документа.
    """
    document = instance
    
    # Шукаємо активний процес для ОІД цього документа
    if not hasattr(document.oid, 'active_process'):
        return # У цього ОІД немає активного процесу

    oid_process = document.oid.active_process
    
    # Шукаємо крок, який очікує на цей тип документа і цей статус
    try:
        step_instance = OIDProcessStepInstance.objects.get(
            oid_process=oid_process,
            status=ProcessStepStatusChoices.PENDING,
            process_step__document_type=document.document_type,
            process_step__trigger_document_status=document.processing_status
        )
    except OIDProcessStepInstance.DoesNotExist:
        return # Не знайдено відповідного кроку для оновлення
    except OIDProcessStepInstance.MultipleObjectsReturned:
        # Обробка випадку, коли знайдено декілька кроків (малоймовірно при правильному дизайні)
        return

    # Оновлюємо крок
    step_instance.status = ProcessStepStatusChoices.COMPLETED
    step_instance.completed_at = timezone.now()
    step_instance.linked_document = document
    step_instance.save()
    
    # --- Специфічна логіка для кроку 2 з вашого шаблону ---
    # Якщо завершено крок "Відправка реєстраційних номерів до вч"
    if step_instance.process_step.name == "Відправка реєстраційних номерів до вч":
        # Змінюємо статус ОІД на "Активний"
        oid_to_update = document.oid
        oid_to_update.status = OIDStatusChoices.ACTIVE
        oid_to_update.save(update_fields=['status'])
        print(f"DEBUG: Статус ОІД {oid_to_update.cipher} змінено на Активний.")
        

@receiver(post_save, sender=Document)
def check_work_request_item_completion_on_document_save(sender, instance, created, **kwargs):
    """
    Перевіряє завершеність WorkRequestItem при збереженні документа.
    """
    document = instance
    
    # Якщо документ пов'язаний з WorkRequestItem
    if document.work_request_item:
        wri = document.work_request_item
        print(f"[SIGNAL] Document saved for WRI ID {wri.id}. Checking completion status...")
        wri.check_and_update_status_based_on_documents()
        

# У signals.py
@receiver(post_save, sender=Document)
def check_work_request_item_on_document_save(sender, instance, created, **kwargs):
    """
    Перевіряє та оновлює статус WorkRequestItem при збереженні документа.
    """
    document = instance
    
    # Якщо документ пов'язаний з WorkRequestItem
    if document.work_request_item:
        wri = document.work_request_item
        print(f"[SIGNAL] Document ID {document.id} saved for WRI ID {wri.id}. Triggering status check...")
        wri.check_and_update_status_based_on_documents()
    else:
        print(f"[SIGNAL] Document ID {document.id} saved but not linked to any WorkRequestItem.")


@receiver(post_save, sender='oids.AttestationRegistration')
def check_items_on_attestation_registration_save(sender, instance, created, **kwargs):
    """
    Перевіряє WorkRequestItems при створенні/оновленні відправки на реєстрацію.
    """
    registration = instance
    
    # Отримуємо всі документи, відправлені в цій реєстрації
    sent_docs = Document.objects.filter(attestation_registration_sent=registration)
    
    print(f"[SIGNAL] AttestationRegistration ID {registration.id} saved. Checking {sent_docs.count()} documents...")
    
    for doc in sent_docs:
        if doc.work_request_item:
            print(f"[SIGNAL] Checking WRI ID {doc.work_request_item.id} for document ID {doc.id}")
            doc.work_request_item.check_and_update_status_based_on_documents()


@receiver(post_save, sender='oids.TripResultForUnit')
def check_items_on_trip_result_save(sender, instance, created, **kwargs):
    """
    Перевіряє WorkRequestItems при створенні/оновленні відправки результатів у в/ч.
    """
    trip_result = instance
    
    # Отримуємо всі документи, відправлені в цьому результаті відрядження
    sent_docs = trip_result.documents.all()
    
    print(f"[SIGNAL] TripResultForUnit ID {trip_result.id} saved. Checking {sent_docs.count()} documents...")
    
    for doc in sent_docs:
        if doc.work_request_item:
            print(f"[SIGNAL] Checking WRI ID {doc.work_request_item.id} for document ID {doc.id}")
            doc.work_request_item.check_and_update_status_based_on_documents()
            

