# oids/views.py
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import (Unit, OID, TerritorialManagement, OIDStatusChoices, WorkTypeChoices, 
    Document, DocumentType, WorkRequest, WorkRequestItem, Trip
)
from .forms import (WorkRequestForm, DocumentForm, TripForm
)
# ... (інші імпорти, якщо потрібні)
# ... (TerritorialManagement, Unit, OID, 
    # Document, DocumentType, Trip, Person, OIDStatusChoices,
    # WorkRequestStatusChoices, WorkTypeChoices, TechnicalTask,
    # AttestationRegistration, AttestationItem, AttestationResponse, TripResultForUnit)


def ajax_load_oids_for_unit(request):
    unit_id = request.GET.get('unit') # Назва параметра з твого JS
    oids_data = []
    if unit_id:
        # Фільтруй ОІД за необхідними статусами для випадаючого списку
        oids = OID.objects.filter(unit__id=unit_id).order_by('cipher') 
        for oid in oids:
            # Формуй дані так, як очікує твій transformItem у JS
            oids_data.append({
                'id': oid.id, 
                'name': f"{oid.cipher} ({oid.get_oid_type_display()}) - {oid.full_name or oid.unit.city}"
            })
    return JsonResponse(list(oids_data), safe=False) # safe=False для списків

# Твоя допоміжна функція
def get_last_document_expiration_date(oid, document_name_keyword, work_type_choice=None):
    try:
        doc_type_filters = Q(name__icontains=document_name_keyword)
        if work_type_choice:
            doc_type_filters &= Q(work_type=work_type_choice)
        relevant_doc_type = DocumentType.objects.filter(doc_type_filters).first()
        if not relevant_doc_type:
            return None
        last_document = Document.objects.filter(
            oid=oid,
            document_type=relevant_doc_type,
            expiration_date__isnull=False
        ).order_by('-work_date', '-process_date').first()
        return last_document.expiration_date if last_document else None
    except Exception as e:
        print(f"Помилка get_last_document_expiration_date для ОІД {oid.cipher if oid else 'N/A'}: {e}")
        return None

def main_dashboard(request):
    # Кнопки керування
    add_request_url = '#' # reverse('add_work_request_view_name')
    plan_trip_url = '#'   # reverse('plan_trip_view_name')
    add_document_processing_url = '#' # reverse('add_document_processing_view_name')

    # 1. Стовпчик: Військові частини
    all_units = Unit.objects.select_related('territorial_management').order_by('name')
    
    selected_unit_id = request.GET.get('unit')
    selected_unit = None

    oids_creating_list = []
    oids_active_list = []
    oids_cancelled_list = []

    if selected_unit_id:
        try:
            selected_unit = Unit.objects.select_related('territorial_management').get(pk=selected_unit_id)
            # Фільтруємо ОІД для обраної ВЧ
            oids_for_selected_unit = OID.objects.filter(unit=selected_unit).select_related('unit').order_by('cipher')
            
            for oid_instance in oids_for_selected_unit:
                if oid_instance.status in [OIDStatusChoices.NEW, OIDStatusChoices.RECEIVED_REQUEST, OIDStatusChoices.RECEIVED_TZ]:
                    oids_creating_list.append(oid_instance)
                elif oid_instance.status == OIDStatusChoices.ACTIVE:
                    oid_instance.ik_expiration_date = get_last_document_expiration_date(oid_instance, 'Висновок', WorkTypeChoices.IK)
                    oid_instance.attestation_expiration_date = get_last_document_expiration_date(oid_instance, 'Акт атестації', WorkTypeChoices.ATTESTATION)
                    oid_instance.prescription_expiration_date = get_last_document_expiration_date(oid_instance, 'Припис')
                    oids_active_list.append(oid_instance)
                elif oid_instance.status in [OIDStatusChoices.CANCELED, OIDStatusChoices.TERMINATED]:
                    oids_cancelled_list.append(oid_instance)
        except Unit.DoesNotExist:
            selected_unit_id = None # Скидаємо, якщо ВЧ не знайдено
            # Можна додати повідомлення для користувача
    
    context = {
        'add_request_url': add_request_url,
        'plan_trip_url': plan_trip_url,
        'add_document_processing_url': add_document_processing_url,
        'all_units': all_units, # Для випадаючого списку ВЧ
        'selected_unit_id': int(selected_unit_id) if selected_unit_id else None,
        'selected_unit_object': selected_unit, # Передаємо об'єкт обраної ВЧ
        'oids_creating': oids_creating_list,
        'oids_active': oids_active_list,
        'oids_cancelled': oids_cancelled_list,
    }
    return render(request, 'oids/main_dashboard.html', context)

# --- AJAX Views (потрібно створити ці view для роботи filtering_dynamic.js) ---

def ajax_load_oids_for_unit(request):
    unit_id = request.GET.get('unit_id') # Або 'unit', як у твоєму JS F1
    oids_data = []
    if unit_id:
        # Фільтруємо ОІД за статусом "активний" або "створюється",
        # щоб користувач не міг обрати вже скасований ОІД для нової роботи, наприклад.
        # Або ж повертати всі, а логіку вибору реалізувати на фронтенді/формах.
        # Тут повертаємо всі для простоти, але з активним статусом для прикладу
        oids = OID.objects.filter(
            unit__id=unit_id, 
            status__in=[OIDStatusChoices.ACTIVE, OIDStatusChoices.NEW, OIDStatusChoices.RECEIVED_REQUEST, OIDStatusChoices.RECEIVED_TZ]
        ).order_by('cipher')
        for oid in oids:
            # `transformItem: item => ({ value: item.id, label: item.name })` з твого JS
            # тут name - це поле моделі OID, яке містить зрозумілу назву/шифр
            oids_data.append({'id': oid.id, 'name': f"{oid.cipher} ({oid.get_oid_type_display()}) - {oid.full_name or oid.unit.city}"}) 
    return JsonResponse(oids_data, safe=False)

# ... (view oid_detail_view залишається схожим, як ми обговорювали раніше)
# ... (view-заглушки для форм теж)

def oid_detail_view(request, oid_id):
    # (Код з попереднього повідомлення, переконайся, що він актуальний з моделями)
    oid = get_object_or_404(
        OID.objects.select_related(
            'unit',
            'unit__territorial_management'
        ),
        pk=oid_id
    )
    # ... (решта логіки для збору даних) ...
    
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


# --- Представлення для форм ---

def add_work_request(request):
    if request.method == 'POST':
        form = WorkRequestForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main_dashboard')
    else:
        form = WorkRequestForm()
    return render(request, 'oids/forms/add_work_request_form.html', {'form': form})

def plan_trip(request):
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save(commit=False)
            trip.save() # Зберігаємо Trip спочатку, щоб отримати pk
            form.save_m2m() # Зберігаємо ManyToMany зв'язки
            return redirect('main_dashboard')
    else:
        form = TripForm()
    return render(request, 'oids/forms/plan_trip_form.html', {'form': form})

def add_document_processing(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST)
        if form.is_valid():
            form.save()
            # Оновлення статусу ОІД після додавання документів
            oid = form.cleaned_data['oid']
            # Припустимо, що додавання "Акту атестації" змінює статус на "Атестована"
            # Або "Висновок ІК" може змінювати на "В експлуатації"
            # Це вже бізнес-логіка, яку потрібно визначити
            # Для прикладу, змінюємо статус ОІД на "В експлуатації" після додавання документа
            # Це дуже спрощено, в реальному проекті потрібна складніша логіка
            if oid.status != OIDStatusChoices.ACTIVE:
                oid.status = OIDStatusChoices.ACTIVE # Або інший логічний статус
                oid.save()
                # Можна також створити запис в OIDStatusChange
                # OIDStatusChange.objects.create(
                #     oid=oid,
                #     old_status=old_status,
                #     new_status=oid.status,
                #     reason="Документ опрацьовано",
                #     changed_by=request.user if request.user.is_authenticated else None, # Припустимо, користувач залогінений
                #     initiating_document=form.instance
                # )

            return redirect('main_dashboard')
    else:
        form = DocumentForm()
    return render(request, 'oids/forms/add_document_processing_form.html', {'form': form})