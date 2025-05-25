# oids/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse # Не забувай імпортувати
from .models import (
    Unit, OID, TerritorialManagement, # Додав TerritorialManagement
    OIDStatusChoices, WorkTypeChoices, Document, DocumentType,
    WorkRequest, WorkRequestItem, Trip, Person, TechnicalTask,
    # Додай інші моделі, якщо вони потрібні для інших view
)
from django.db.models import Q # Для складних запитів

# Твоя допоміжна функція (залишається без змін, але буде викликатися в AJAX view)
def get_last_document_expiration_date(oid, document_name_keyword, work_type_choice=None):
    try:
        doc_type_filters = Q(name__icontains=document_name_keyword)
        if work_type_choice:
            doc_type_filters &= Q(work_type=work_type_choice)
        
        # Шукаємо DocumentType, який відповідає ключовому слову та типу роботи
        # Якщо тип роботи не вказано, але є кілька типів документів з однаковою назвою
        # (наприклад, "Припис" для Атестації і "Припис" для ІК), це може потребувати уточнення
        # або більш точних ключових слів.
        relevant_doc_type_qs = DocumentType.objects.filter(doc_type_filters)
        if not relevant_doc_type_qs.exists():
            # print(f"Debug: DocumentType не знайдено для '{document_name_keyword}' та work_type '{work_type_choice}'")
            return None
        
        # Якщо знайдено кілька, можливо, потрібна додаткова логіка вибору
        # Для простоти беремо перший знайдений, але це може бути не завжди коректно.
        relevant_doc_type = relevant_doc_type_qs.first()

        last_document = Document.objects.filter(
            oid=oid,
            document_type=relevant_doc_type,
            expiration_date__isnull=False
        ).order_by('-work_date', '-process_date').first()
        
        # print(f"Debug: OID: {oid.cipher}, DocType: {relevant_doc_type.name}, LastDoc: {last_document}, ExpDate: {last_document.expiration_date if last_document else 'N/A'}")
        return last_document.expiration_date if last_document else None
    except Exception as e:
        print(f"Помилка get_last_document_expiration_date для ОІД {oid.cipher if oid else 'N/A'} ({document_name_keyword}): {e}")
        return None

def main_dashboard(request):
    """
    Головна сторінка. Завантажує список ВЧ.
    ОІДи будуть завантажуватися через AJAX.
    """
    # Кнопки керування (посилання на відповідні форми/views)
    # Переконайся, що ці URL-и існують в твоїх urls.py
    # і ведуть на реальні views для додавання/планування
    try:
        add_request_url = reverse('oids:add_work_request_view_name') # Приклад name='add_work_request_view_name' в urls.py
        plan_trip_url = reverse('oids:plan_trip_view_name')
        add_document_processing_url = reverse('oids:add_document_processing_view_name')
    except Exception as e: # Обробка помилки, якщо URL-и ще не визначені
        print(f"Помилка реверсу URL: {e}. Перевірте ваші urls.py.")
        add_request_url = '#'
        plan_trip_url = '#'
        add_document_processing_url = '#'


    all_units = Unit.objects.select_related('territorial_management').order_by('name')
    
    # selected_unit_id буде використовуватися JavaScript для початкового завантаження,
    # або якщо користувач переходить за прямим посиланням з GET-параметром.
    selected_unit_id_str = request.GET.get('unit')
    selected_unit_object = None
    if selected_unit_id_str:
        try:
            selected_unit_object = Unit.objects.get(pk=int(selected_unit_id_str))
        except (ValueError, Unit.DoesNotExist):
            selected_unit_object = None # або обробити помилку

    context = {
        'add_request_url': add_request_url,
        'plan_trip_url': plan_trip_url,
        'add_document_processing_url': add_document_processing_url,
        'all_units': all_units,
        'selected_unit_id': int(selected_unit_id_str) if selected_unit_id_str else None,
        'selected_unit_object': selected_unit_object, 
        # Списки ОІД тепер будуть завантажуватися через AJAX, тому їх тут немає
    }
    return render(request, 'oids/main_dashboard.html', context)

def ajax_load_oids_for_unit_categorized(request):
    """
    AJAX view для завантаження ОІДів обраної військової частини,
    розділених на категорії.
    """
    unit_id = request.GET.get('unit_id') # Параметр, який передає JS
    data = {
        'creating': [],
        'active': [],
        'cancelled': []
    }

    if unit_id:
        try:
            # Оптимізуємо запит, обираючи тільки потрібні поля для JSON відповіді
            # та пов'язані дані, якщо вони потрібні для відображення
            oids_for_unit = OID.objects.filter(unit__id=unit_id)\
                                     .select_related('unit')\
                                     .values('id', 'cipher', 'full_name', 'status', 'oid_type', 'unit__city')\
                                     .order_by('cipher')
            
            # Визначення типів документів для ІК, Атестації, Припису один раз
            ik_doc_type_name_keyword = 'Висновок' # Або більш точно "Висновок ІК"
            attestation_doc_type_name_keyword = 'Акт атестації'
            prescription_doc_type_name_keyword = 'Припис'

            for oid_data in oids_for_unit:
                # Створюємо тимчасовий об'єкт OID для передачі в get_last_document_expiration_date,
                # або модифікуємо функцію, щоб вона приймала словник oid_data
                temp_oid_obj = OID(pk=oid_data['id'], cipher=oid_data['cipher']) # Мінімально необхідні поля для функції

                oid_item = {
                    'id': oid_data['id'],
                    'cipher': oid_data['cipher'],
                    'full_name': oid_data['full_name'] or oid_data['unit__city'], # Використовуємо місто, якщо назва порожня
                    'oid_type_display': dict(OIDTypeChoices.choices).get(oid_data['oid_type'], oid_data['oid_type']),
                    'status_display': dict(OIDStatusChoices.choices).get(oid_data['status'], oid_data['status']),
                    # Посилання на детальну сторінку
                    'detail_url': reverse('oids:oid_detail_view_name', args=[oid_data['id']]) # Заміни 'oid_detail_view_name'
                }

                if oid_data['status'] in [OIDStatusChoices.NEW, OIDStatusChoices.RECEIVED_REQUEST, OIDStatusChoices.RECEIVED_TZ]:
                    # Тут можна додати логіку перевірки наявності активних заявок, якщо потрібно
                    data['creating'].append(oid_item)
                elif oid_data['status'] == OIDStatusChoices.ACTIVE:
                    oid_item['ik_expiration_date'] = get_last_document_expiration_date(temp_oid_obj, ik_doc_type_name_keyword, WorkTypeChoices.IK)
                    oid_item['attestation_expiration_date'] = get_last_document_expiration_date(temp_oid_obj, attestation_doc_type_name_keyword, WorkTypeChoices.ATTESTATION)
                    oid_item['prescription_expiration_date'] = get_last_document_expiration_date(temp_oid_obj, prescription_doc_type_name_keyword) # Може бути для обох типів робіт
                    data['active'].append(oid_item)
                elif oid_data['status'] in [OIDStatusChoices.CANCELED, OIDStatusChoices.TERMINATED]:
                    data['cancelled'].append(oid_item)
        except ValueError: # Якщо unit_id не є числом
            return JsonResponse({'error': 'Невірний ID військової частини'}, status=400)
        except Exception as e:
            print(f"Серверна помилка в ajax_load_oids_for_unit_categorized: {e}")
            return JsonResponse({'error': 'Серверна помилка'}, status=500)
            
    return JsonResponse(data)

# Ваш ajax_load_oids_for_unit (якщо потрібен окремо для простого списку ОІДів, наприклад, для форм)
def ajax_load_oids_for_unit(request):
    unit_id = request.GET.get('unit_id') # або 'unit'
    oids_data = []
    if unit_id:
        try:
            # Фільтруємо ОІД за потрібними статусами для випадаючого списку
            oids = OID.objects.filter(
                unit__id=unit_id,
                status__in=[
                    OIDStatusChoices.ACTIVE, 
                    OIDStatusChoices.NEW, 
                    OIDStatusChoices.RECEIVED_REQUEST, 
                    OIDStatusChoices.RECEIVED_TZ
                ]
            ).order_by('cipher')
            for oid in oids:
                oids_data.append({
                    'id': oid.id, 
                    'name': f"{oid.cipher} ({oid.get_oid_type_display()}) - {oid.full_name or oid.unit.city}"
                })
        except ValueError:
             return JsonResponse([], safe=False) # Повертаємо порожній список при помилці ID
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