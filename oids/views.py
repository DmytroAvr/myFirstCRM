# oids/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse # Не забувай імпортувати
from .models import (
    Unit, OID, TerritorialManagement, 
    OIDStatusChoices, WorkTypeChoices, Document, DocumentType,
    WorkRequest, WorkRequestStatusChoices, WorkRequestItem, Trip,TripResultForUnit, Person, TechnicalTask,
    AttestationRegistration, AttestationItem, AttestationResponse
)

from django.db.models import Q, Max, Prefetch

# Твоя допоміжна функція (залишається без змін, але буде викликатися в AJAX view)
def get_last_document_expiration_date(oid_instance, document_name_keyword, work_type_choice=None):
    try:
        doc_type_filters = Q(name__icontains=document_name_keyword)
        if work_type_choice:
            doc_type_filters &= Q(work_type=work_type_choice)
        
        relevant_doc_type_qs = DocumentType.objects.filter(doc_type_filters)
        if not relevant_doc_type_qs.exists():
            return None
        relevant_doc_type = relevant_doc_type_qs.first()

        last_document = Document.objects.filter(
            oid=oid_instance, # Використовуємо переданий екземпляр OID
            document_type=relevant_doc_type,
            expiration_date__isnull=False
        ).order_by('-work_date', '-process_date').first()
        
        return last_document.expiration_date if last_document else None
    except Exception as e:
        print(f"Помилка get_last_document_expiration_date для ОІД {oid_instance.cipher if oid_instance else 'N/A'} ({document_name_keyword}): {e}")
        return None
    

def main_dashboard(request):
    """
    Головна сторінка. Фільтрація ВЧ -> ОІД відбувається на сервері 
    через перезавантаження сторінки.
    """
    try:
        add_request_url = reverse('oids:add_work_request_view_name') 
        plan_trip_url = reverse('oids:plan_trip_view_name')
        add_document_processing_url = reverse('oids:add_document_processing_view_name')
    except Exception:
        add_request_url, plan_trip_url, add_document_processing_url = '#', '#', '#'

    all_units = Unit.objects.select_related('territorial_management').order_by('name')
    
    selected_unit_id_str = request.GET.get('unit')
    selected_unit_object = None
    
    oids_creating_list = []
    oids_active_list = []
    oids_cancelled_list = []

    if selected_unit_id_str:
        try:
            selected_unit_id = int(selected_unit_id_str)
            selected_unit_object = Unit.objects.get(pk=selected_unit_id)
            
            oids_for_selected_unit = OID.objects.filter(unit_id=selected_unit_id)\
                                              .select_related('unit')\
                                              .order_by('cipher')

            for oid_instance in oids_for_selected_unit:
                oid_item_data = {
                    'id': oid_instance.id,
                    'cipher': oid_instance.cipher,
                    'full_name': oid_instance.full_name or oid_instance.unit.city,
                    'oid_type_display': oid_instance.get_oid_type_display(),
                    'status_display': oid_instance.get_status_display(),
                    'detail_url': reverse('oids:oid_detail_view_name', args=[oid_instance.id])
                }
                if oid_instance.status in [OIDStatusChoices.NEW, OIDStatusChoices.RECEIVED_REQUEST, OIDStatusChoices.RECEIVED_TZ]:
                    oids_creating_list.append(oid_item_data)
                elif oid_instance.status == OIDStatusChoices.ACTIVE:
                    oid_item_data['ik_expiration_date'] = get_last_document_expiration_date(oid_instance, 'Висновок', WorkTypeChoices.IK)
                    oid_item_data['attestation_expiration_date'] = get_last_document_expiration_date(oid_instance, 'Акт атестації', WorkTypeChoices.ATTESTATION)
                    oid_item_data['prescription_expiration_date'] = get_last_document_expiration_date(oid_instance, 'Припис')
                    oids_active_list.append(oid_item_data)
                elif oid_instance.status in [OIDStatusChoices.CANCELED, OIDStatusChoices.TERMINATED]:
                    oids_cancelled_list.append(oid_item_data)
        except (ValueError, Unit.DoesNotExist):
            selected_unit_object = None 
            # Можна додати повідомлення про помилку, якщо unit_id невірний
            # messages.error(request, "Обрана військова частина не знайдена.")

    context = {
        'add_request_url': add_request_url,
        'plan_trip_url': plan_trip_url,
        'add_document_processing_url': add_document_processing_url,
        'all_units': all_units,
        'selected_unit_id': selected_unit_id_str, # Передаємо рядок для порівняння в шаблоні
        'selected_unit_object': selected_unit_object,
        'oids_creating': oids_creating_list,
        'oids_active': oids_active_list,
        'oids_cancelled': oids_cancelled_list,
    }
    return render(request, 'oids/main_dashboard.html', context)

# old. give ino by vocabulary
# def ajax_load_oids_for_unit_categorized(request):
#     """
#     AJAX view для завантаження ОІДів обраної військової частини,
#     розділених на категорії.
#     """
#     unit_id = request.GET.get('unit_id') # Параметр, який передає JS
#     data = {
#         'creating': [],
#         'active': [],
#         'cancelled': []
#     }

#     if unit_id:
#         try:
#             # Оптимізуємо запит, обираючи тільки потрібні поля для JSON відповіді
#             # та пов'язані дані, якщо вони потрібні для відображення
#             oids_for_unit = OID.objects.filter(unit__id=unit_id)\
#                                      .select_related('unit')\
#                                      .values('id', 'cipher', 'full_name', 'status', 'oid_type', 'unit__city')\
#                                      .order_by('cipher')
            
#             # Визначення типів документів для ІК, Атестації, Припису один раз
#             ik_doc_type_name_keyword = 'Висновок' # Або більш точно "Висновок ІК"
#             attestation_doc_type_name_keyword = 'Акт атестації'
#             prescription_doc_type_name_keyword = 'Припис'

#             for oid_data in oids_for_unit:
#                 # Створюємо тимчасовий об'єкт OID для передачі в get_last_document_expiration_date,
#                 # або модифікуємо функцію, щоб вона приймала словник oid_data
#                 temp_oid_obj = OID(pk=oid_data['id'], cipher=oid_data['cipher']) # Мінімально необхідні поля для функції

#                 oid_item = {
#                     'id': oid_data['id'],
#                     'cipher': oid_data['cipher'],
#                     'full_name': oid_data['full_name'] or oid_data['unit__city'], # Використовуємо місто, якщо назва порожня
#                     'oid_type_display': dict(OIDTypeChoices.choices).get(oid_data['oid_type'], oid_data['oid_type']),
#                     'status_display': dict(OIDStatusChoices.choices).get(oid_data['status'], oid_data['status']),
#                     # Посилання на детальну сторінку
#                     'detail_url': reverse('oids:oid_detail_view_name', args=[oid_data['id']]) # Заміни 'oid_detail_view_name'
#                 }

#                 if oid_data['status'] in [OIDStatusChoices.NEW, OIDStatusChoices.RECEIVED_REQUEST, OIDStatusChoices.RECEIVED_TZ]:
#                     # Тут можна додати логіку перевірки наявності активних заявок, якщо потрібно
#                     data['creating'].append(oid_item)
#                 elif oid_data['status'] == OIDStatusChoices.ACTIVE:
#                     oid_item['ik_expiration_date'] = get_last_document_expiration_date(temp_oid_obj, ik_doc_type_name_keyword, WorkTypeChoices.IK)
#                     oid_item['attestation_expiration_date'] = get_last_document_expiration_date(temp_oid_obj, attestation_doc_type_name_keyword, WorkTypeChoices.ATTESTATION)
#                     oid_item['prescription_expiration_date'] = get_last_document_expiration_date(temp_oid_obj, prescription_doc_type_name_keyword) # Може бути для обох типів робіт
#                     data['active'].append(oid_item)
#                 elif oid_data['status'] in [OIDStatusChoices.CANCELED, OIDStatusChoices.TERMINATED]:
#                     data['cancelled'].append(oid_item)
#         except ValueError: # Якщо unit_id не є числом
#             return JsonResponse({'error': 'Невірний ID військової частини'}, status=400)
#         except Exception as e:
#             print(f"Серверна помилка в ajax_load_oids_for_unit_categorized: {e}")
#             return JsonResponse({'error': 'Серверна помилка'}, status=500)
            
#     return JsonResponse(data)

# changede by gemeni. перейшли від передачі словників до передачі повних екземплярів моделі OID у функцію get_last_document_expiration_date. Це важливо для коректної роботи сервера, незалежно від фронтенд-фільтрації.
def ajax_load_oids_for_unit_categorized(request):
    unit_id_str = request.GET.get('unit_id')
    data = {
        'creating': [],
        'active': [],
        'cancelled': []
    }

    if unit_id_str:
        try:
            unit_id = int(unit_id_str)
            # Замість .values(), отримуємо повні об'єкти OID, щоб передавати їх у helper
            oids_for_unit_qs = OID.objects.filter(unit__id=unit_id)\
                                        .select_related('unit', 'unit__territorial_management')\
                                        .order_by('cipher')

            for oid_instance in oids_for_unit_qs: # Тепер це повний екземпляр OID
                oid_item = {
                    'id': oid_instance.id,
                    'cipher': oid_instance.cipher,
                    'full_name': oid_instance.full_name or oid_instance.unit.city,
                    'oid_type_display': oid_instance.get_oid_type_display(), # Використовуємо метод моделі
                    'status_display': oid_instance.get_status_display(),   # Використовуємо метод моделі
                    'detail_url': reverse('oids:oid_detail_view_name', args=[oid_instance.id])
                }

                if oid_instance.status in [OIDStatusChoices.NEW, OIDStatusChoices.RECEIVED_REQUEST, OIDStatusChoices.RECEIVED_TZ]:
                    data['creating'].append(oid_item)
                elif oid_instance.status == OIDStatusChoices.ACTIVE:
                    # Тепер передаємо повний екземпляр oid_instance
                    oid_item['ik_expiration_date'] = get_last_document_expiration_date(oid_instance, 'Висновок', WorkTypeChoices.IK)
                    oid_item['attestation_expiration_date'] = get_last_document_expiration_date(oid_instance, 'Акт атестації', WorkTypeChoices.ATTESTATION)
                    oid_item['prescription_expiration_date'] = get_last_document_expiration_date(oid_instance, 'Припис')
                    data['active'].append(oid_item)
                elif oid_instance.status in [OIDStatusChoices.CANCELED, OIDStatusChoices.TERMINATED]:
                    data['cancelled'].append(oid_item)
        
        except ValueError:
            return JsonResponse({'error': 'Невірний ID військової частини'}, status=400)
        except Exception as e:
            # Виводимо помилку в консоль Django для дебагу
            print(f"SERVER ERROR in ajax_load_oids_for_unit_categorized: {type(e).__name__} - {e}")
            import traceback
            traceback.print_exc() # Друкує повний трейсбек
            return JsonResponse({'error': f'Серверна помилка: {type(e).__name__}'}, status=500)
            
    return JsonResponse(data)


# Ваш ajax_load_oids_for_unit (якщо потрібен окремо для простого списку ОІДів, наприклад, для форм)

# AJAX view для завантаження ОІДів для Select2 у формах (якщо потрібно)
# Цей view НЕ використовується для оновлення списків ОІД на головній панелі в цьому сценарії
def ajax_load_oids_for_unit(request):
    unit_id = request.GET.get('unit_id') # Або 'unit', залежно від JS
    oids_data = []
    if unit_id:
        try:
            oids = OID.objects.filter(
                unit__id=unit_id,
                status__in=[OIDStatusChoices.ACTIVE, OIDStatusChoices.NEW, 
                            OIDStatusChoices.RECEIVED_REQUEST, OIDStatusChoices.RECEIVED_TZ]
            ).order_by('cipher')
            for oid in oids:
                oids_data.append({
                    'id': oid.id, 
                    # 'name' або 'text' - залежно від того, що очікує transformItem або Select2
                    'name': f"{oid.cipher} ({oid.get_oid_type_display()}) - {oid.full_name or oid.unit.city}" 
                })
        except ValueError:
            pass # unit_id не є числом
    return JsonResponse(list(oids_data), safe=False)

# ... (решта ваших views: oid_detail_view, форми для додавання тощо) ...
# Не забудьте додати oid_detail_view з попередньої відповіді.
def oid_detail_view(request, oid_id):
    oid = get_object_or_404(
        OID.objects.select_related(
            'unit',
            'unit__territorial_management'
        ),
        pk=oid_id
    )
    
    status_changes = oid.status_changes.select_related(
        'initiating_document__document_type',
        'changed_by'
    ).order_by('-changed_at')

    work_request_items = oid.work_request_items.select_related(
        'request',
        'request__unit'
    ).order_by('-request__incoming_date')
    
    work_requests_for_oid = WorkRequest.objects.filter(
        items__oid=oid
    ).distinct().order_by('-incoming_date')

    technical_tasks = oid.technical_tasks.select_related('reviewed_by').order_by('-input_date')

    documents = oid.documents.select_related(
        'document_type',
        'author',
        'work_request_item__request'
    ).order_by('-process_date', '-work_date')

    trips_for_oid = oid.trips.prefetch_related(
        'units',
        'persons',
        'work_requests'
    ).order_by('-start_date')
    
    attestation_registrations_for_oid = AttestationRegistration.objects.filter(
        attestation_items__oid=oid
    ).prefetch_related(
        Prefetch('attestation_items', queryset=AttestationItem.objects.filter(oid=oid).select_related('document__document_type')),
        'response'
    ).distinct().order_by('-process_date')
    
    trip_results_for_oid = TripResultForUnit.objects.filter(
        oids=oid
    ).select_related('trip').prefetch_related('units', 'documents__document_type').order_by('-process_date')

    last_attestation_expiration = get_last_document_expiration_date(oid, 'Акт атестації', WorkTypeChoices.ATTESTATION)
    last_ik_expiration = get_last_document_expiration_date(oid, 'Висновок', WorkTypeChoices.IK)
    last_prescription_expiration = get_last_document_expiration_date(oid, 'Припис')

    context = {
        'oid': oid,
        'status_changes': status_changes,
        'work_requests_for_oid': work_requests_for_oid,
        'work_request_items_for_oid': work_request_items,
        'technical_tasks': technical_tasks,
        'documents': documents,
        'trips_for_oid': trips_for_oid,
        'attestation_registrations_for_oid': attestation_registrations_for_oid,
        'trip_results_for_oid': trip_results_for_oid,
        'last_attestation_expiration': last_attestation_expiration,
        'last_ik_expiration': last_ik_expiration,
        'last_prescription_expiration': last_prescription_expiration,
    }
    return render(request, 'oids/oid_detail.html', context)