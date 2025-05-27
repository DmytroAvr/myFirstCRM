# :\myFirstCRM\oids\views.py
from django.shortcuts import render, get_object_or_404, redirect
from django_tomselect.autocompletes import AutocompleteModelView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import JsonResponse
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q, Max, Prefetch, Count
from .models import (
    Unit, UnitGroup, OID, OIDStatusChange, TerritorialManagement, Document, DocumentType,
    WorkRequest, WorkRequestItem, Trip,TripResultForUnit, Person, TechnicalTask,
    AttestationRegistration, AttestationItem, AttestationResponse,
    
    OIDTypeChoices, OIDStatusChoices, SecLevelChoices, WorkRequestStatusChoices, WorkTypeChoices, DocumentReviewResultChoices
)
from .forms import ( TripForm, DocumentForm, WorkRequestForm, OIDForm
)

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
    unit_id = request.GET.get('unit_id')
    oids_data = []
    if unit_id:
        try:
            # Обираємо активні або ті, що створюються, якщо є таке бізнес-правило
            oids = OID.objects.filter(unit_id=unit_id).order_by('cipher') 
            for oid in oids:
                oids_data.append({
                    'id': oid.id,
                    'cipher': oid.cipher, # Для відображення
                    'full_name': oid.full_name, # Може бути корисним
                    'unit__city': oid.unit.city # Якщо потрібно
                    # Додайте інші поля, якщо вони потрібні для відображення в TomSelect
                })
        except (ValueError, Unit.DoesNotExist):
            pass 
    return JsonResponse(list(oids_data), safe=False)

# oids/urls.py - не забудьте додати:
# path('ajax/load-oids-for-unit/', views.ajax_load_oids_for_unit, name='ajax_load_oids_for_unit'),

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



# ... (main_dashboard, ajax_load_oids_for_unit_categorized, ajax_load_oids_for_unit, oid_detail_view) ...
# Переконайся, що функція get_last_document_expiration_date визначена вище

def plan_trip_view(request):
    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            trip = form.save()
            messages.success(request, f'Відрядження заплановано успішно (ID: {trip.id}).')
            # Оновлюємо статус пов'язаних заявок на "В роботі"
            for work_request in form.cleaned_data.get('work_requests', []):
                if work_request.status == WorkRequestStatusChoices.PENDING:
                    work_request.status = WorkRequestStatusChoices.IN_PROGRESS
                    work_request.save()
                    # Також оновити статус WorkRequestItem, якщо потрібно
                    WorkRequestItem.objects.filter(request=work_request, status=WorkRequestStatusChoices.PENDING)\
                                           .update(status=WorkRequestStatusChoices.IN_PROGRESS)

            return redirect('oids:main_dashboard') # Або на сторінку деталей відрядження
    else:
        form = TripForm()
    
    return render(request, 'oids/forms/plan_trip_form.html', {'form': form, 'page_title': 'Запланувати відрядження'})

def add_document_processing_view(request, oid_id=None, work_request_item_id=None):
    initial_data = {}
    selected_oid = None
    
    if oid_id:
        selected_oid = get_object_or_404(OID, pk=oid_id)
        initial_data['oid'] = selected_oid
    
    if work_request_item_id:
        work_request_item_instance = get_object_or_404(WorkRequestItem, pk=work_request_item_id)
        initial_data['work_request_item'] = work_request_item_instance
        if not selected_oid: # Якщо OID не передано, беремо з WorkRequestItem
            selected_oid = work_request_item_instance.oid
            initial_data['oid'] = selected_oid

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES, initial_oid=selected_oid) # Передаємо initial_oid для фільтрації
        if form.is_valid():
            document = form.save()
            messages.success(request, f'Документ "{document.document_type.name}" №{document.document_number} успішно додано.')
            
            # Оновлення статусу WorkRequestItem, якщо документ пов'язаний з ним
            if document.work_request_item:
                # Перевіряємо, чи всі обов'язкові документи для цього WorkRequestItem вже є
                # Ця логіка може бути складною і залежить від бізнес-правил
                # Поки що просто змінюємо статус, якщо він був "в роботі"
                item = document.work_request_item
                if item.status == WorkRequestStatusChoices.IN_PROGRESS:
                     # Потрібно визначити, коли саме елемент заявки вважається виконаним
                     # Наприклад, коли додано певний ключовий документ
                     # Або коли всі обов'язкові документи для цього типу робіт по ОІД є.
                     # Тут поки що не змінюємо статус автоматично, це потребує деталізації правил.
                     pass

            # Оновлення статусу ОІД (спрощена логіка)
            # Цю логіку краще винести в сигнали або методи моделі OID
            current_oid = document.oid
            # Приклад: якщо додано "Акт атестації", змінюємо статус ОІД
            if document.document_type.name.lower().startswith('акт атестації') and current_oid.status != OIDStatusChoices.ACTIVE:
                # Потрібно створити запис в OIDStatusChange
                current_oid.status = OIDStatusChoices.ACTIVE # Або ATTESTED, залежно від воркфлоу
                current_oid.save()
                messages.info(request, f'Статус ОІД "{current_oid.cipher}" оновлено на "{current_oid.get_status_display()}".')

            return redirect('oids:oid_detail_view_name', oid_id=document.oid.id)
    else:
        form = DocumentForm(initial=initial_data, initial_oid=selected_oid)

    return render(request, 'oids/forms/add_document_processing_form.html', {
        'form': form, 
        'page_title': 'Додати опрацювання документів',
        'selected_oid': selected_oid
    })

def add_work_request_view(request):
    # Можна передати початкове значення для ВЧ, якщо воно є в GET-запиті
    initial_data = {}
    unit_id_from_get = request.GET.get('unit')
    if unit_id_from_get:
        initial_data['unit'] = unit_id_from_get

    if request.method == 'POST':
        form = WorkRequestForm(request.POST)
        if form.is_valid():
            form.save() # Метод save форми тепер сам створює WorkRequestItems
            messages.success(request, f'Заявку №{form.instance.incoming_number} успішно створено!')
            return redirect('oids:list_work_requests') # Або на сторінку деталей заявки, або main_dashboard
        else:
            messages.error(request, 'Будь ласка, виправте помилки у формі.')
    else:
        form = WorkRequestForm(initial=initial_data)

    # Передаємо choices для OIDType та OIDStatus, якщо вони потрібні для модального вікна створення OID
    # (якщо модалка рендериться на цій сторінці, а не в base.html)
    # context_data = {
    #     'view': { # Щоб імітувати доступ як у base.html, якщо потрібно
    #         'get_oid_type_choices': OIDTypeChoices.choices,
    #         'get_oid_status_choices': OIDStatusChoices.choices,
    #         'get_sec_level_choices': SecLevelChoices.choices,
    #     }
    # }

    return render(request, 'oids/forms/add_work_request_form.html', {
        'form': form,
        'page_title': 'Створення нової заявки на проведення робіт',
        # **context_data # Якщо передаєте choices
    })
# 
# 
# list info 


def summary_information_hub_view(request):
    """
    Сторінка-хаб з посиланнями на списки об'єктів різних моделей.
    """
    # Список моделей та відповідних їм назв URL для перегляду
    # Ключ 'label' - це те, що побачить користувач
    # Ключ 'url_name' - це name з urls.py для відповідного списку
    model_views = [
        {'label': 'Військові частини', 'url_name': 'oids:list_units'},
        {'label': 'Об\'єкти інформаційної діяльності (ОІД)', 'url_name': 'oids:list_oids'},
        {'label': 'Заявки на проведення робіт', 'url_name': 'oids:list_work_requests'},
        {'label': 'Опрацьовані документи', 'url_name': 'oids:list_documents'},
        {'label': 'Відрядження', 'url_name': 'oids:list_trips'},
        {'label': 'Технічні завдання', 'url_name': 'oids:list_technical_tasks'},
        {'label': 'Надсилання на реєстрацію Актів Атестації', 'url_name': 'oids:list_attestation_registrations'},
        {'label': 'Відповіді Реєстрація Атестації', 'url_name': 'oids:list_attestation_responses'},
        {'label': 'Надсилання до частин пакетів документів', 'url_name': 'oids:list_trip_results_for_units'},
        {'label': 'Історія змін статусу ОІД', 'url_name': 'oids:list_oid_status_changes'},
        {'label': 'Довідник: Територіальні управління', 'url_name': 'oids:list_territorial_managements'},
        {'label': 'Довідник: Групи військових частин', 'url_name': 'oids:list_unit_groups'},
        {'label': 'Довідник: Типи документів', 'url_name': 'oids:list_document_types'},
        {'label': 'Довідник: Виконавці (Особи)', 'url_name': 'oids:list_persons'},
    ]
    context = {
        'page_title': 'Зведена інформація та перегляд даних за розділами',
        'model_views': model_views
    }
    return render(request, 'oids/summary_information_hub.html', context)

def document_list_view(request):
    documents_list = Document.objects.select_related(
        'oid__unit__territorial_management', # Оптимізація для доступу до Unit та OID
        'oid__unit',
        'oid',
        'document_type', 
        'author',
        'work_request_item__request'
    ).order_by('-process_date', '-created_at') # Новіші за датою опрацювання, потім за датою створення

    paginator = Paginator(documents_list, 25) # 25 документів на сторінку
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_title': 'Список опрацьованих документів',
        'documents': page_obj, # Передаємо об'єкт сторінки пагінатора
        'page_obj': page_obj # Для навігації пагінатора
    }
    return render(request, 'oids/lists/document_list.html', context)

def unit_list_view(request):
    units_list_qs = Unit.objects.select_related(
        'territorial_management'
    ).prefetch_related(
        'unit_groups', 
        'oids' 
    ).annotate(
        oid_count=Count('oids')
    )

    # --- Фільтрація ---
    selected_tm_id_str = request.GET.get('territorial_management')
    current_tm_id_int = None # Буде None або int
    if selected_tm_id_str and selected_tm_id_str.isdigit():
        current_tm_id_int = int(selected_tm_id_str)
        units_list_qs = units_list_qs.filter(territorial_management__id=current_tm_id_int)
    
    search_query = request.GET.get('search_query')
    if search_query:
        units_list_qs = units_list_qs.filter(
            Q(code__icontains=search_query) | 
            Q(name__icontains=search_query) | 
            Q(city__icontains=search_query)
        )

    # --- Сортування ---
    sort_by = request.GET.get('sort_by', 'territorial_management__name')
    sort_order = request.GET.get('sort_order', 'asc')

    valid_sort_fields = {
        'code': 'code',
        'name': 'name',
        'city': 'city',
        'tm': 'territorial_management__name',
        'oid_count': 'oid_count',
        'distance': 'distance_from_gu'
    }
    
    order_by_field = valid_sort_fields.get(sort_by, 'territorial_management__name')

    if sort_order == 'desc':
        order_by_field = f'-{order_by_field}'
    
    units_list_qs = units_list_qs.order_by(order_by_field, 'name' if order_by_field != 'name' else 'code')

    paginator = Paginator(units_list_qs, 25) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    territorial_managements_for_filter = TerritorialManagement.objects.all().order_by('name')

    context = {
        'page_title': 'Список військових частин',
        'units': page_obj,
        'page_obj': page_obj,
        'territorial_managements_for_filter': territorial_managements_for_filter,
        'current_tm_id': current_tm_id_int, # Передаємо int або None
        'current_search_query': search_query,
        'current_sort_by': sort_by,
        'current_sort_order': sort_order,
        'is_sorted_desc': sort_order == 'desc',
    }
    return render(request, 'oids/lists/unit_list.html', context)

def territorial_management_list_view(request):
    tm_list_queryset = TerritorialManagement.objects.all().order_by('name')
    
    paginator = Paginator(tm_list_queryset, 25) # 25 записів на сторінку
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Список Територіальних Управлінь',
        'object_list': page_obj, # Універсальне ім'я для використання в pagination.html
        'page_obj': page_obj     # Для самого шаблону пагінації
    }
    return render(request, 'oids/lists/territorial_management_list.html', context)

def unit_group_list_view(request):
    group_list_queryset = UnitGroup.objects.prefetch_related('units').order_by('name') # prefetch_related для units
    
    paginator = Paginator(group_list_queryset, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Список Груп Військових Частин',
        'object_list': page_obj,
        'page_obj': page_obj
    }
    return render(request, 'oids/lists/unit_group_list.html', context)

def person_list_view(request):
    person_list_queryset = Person.objects.all().order_by('full_name')
    
    paginator = Paginator(person_list_queryset, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    context = {
        'page_title': 'Список Виконавців (Осіб)',
        'object_list': page_obj,
        'page_obj': page_obj
    }
    return render(request, 'oids/lists/person_list.html', context)

def document_type_list_view(request):
    doc_type_list_queryset = DocumentType.objects.all().order_by('oid_type', 'work_type', 'name')
    
    paginator = Paginator(doc_type_list_queryset, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    context = {
        'page_title': 'Довідник: Типи документів',
        'object_list': page_obj,
        'page_obj': page_obj
    }
    return render(request, 'oids/lists/document_type_list.html', context)


def oid_list_view(request):
    oid_list_queryset = OID.objects.select_related(
        'unit',  # Завантажуємо пов'язану військову частину
        'unit__territorial_management' # А також ТУ для ВЧ, якщо потрібно (наприклад, для відображення)
    )

    # --- Фільтрація ---
    filter_unit_id_str = request.GET.get('filter_unit')
    filter_oid_type = request.GET.get('filter_oid_type')
    filter_status = request.GET.get('filter_status')
    filter_sec_level = request.GET.get('filter_sec_level')
    search_query = request.GET.get('search_query')

    current_filter_unit_id = None
    if filter_unit_id_str and filter_unit_id_str.isdigit():
        current_filter_unit_id = int(filter_unit_id_str)
        oid_list_queryset = oid_list_queryset.filter(unit__id=current_filter_unit_id)
    
    if filter_oid_type:
        oid_list_queryset = oid_list_queryset.filter(oid_type=filter_oid_type)
    
    if filter_status:
        oid_list_queryset = oid_list_queryset.filter(status=filter_status)

    if filter_sec_level:
        oid_list_queryset = oid_list_queryset.filter(sec_level=filter_sec_level)
    
    if search_query:
        oid_list_queryset = oid_list_queryset.filter(
            Q(cipher__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(room__icontains=search_query) |
            Q(note__icontains=search_query) # Додамо пошук по примітках ОІД
        )

    # --- Сортування ---
    # За замовчуванням сортуємо за датою створення (новіші спочатку), якщо поле created_at існує
    # Перевірте вашу модель OID на наявність поля created_at
    # Якщо у вас є поле created_at = models.DateTimeField(auto_now_add=True)
    sort_by_param = request.GET.get('sort_by', '-created_at') # За замовчуванням - новіші ОІД
    sort_order_from_request = request.GET.get('sort_order', '') # 'asc' або 'desc'

    # Визначаємо напрямок сортування
    # Якщо sort_by_param починається з '-', це вже desc. В іншому випадку дивимося на sort_order_from_request
    actual_sort_order_is_desc = False
    if sort_by_param.startswith('-'):
        actual_sort_order_is_desc = True
        sort_by_param_cleaned = sort_by_param[1:]
    else:
        sort_by_param_cleaned = sort_by_param
        if sort_order_from_request == 'desc':
            actual_sort_order_is_desc = True
    
    valid_sort_fields = {
        'unit': 'unit__code',
        'cipher': 'cipher',
        'full_name': 'full_name',
        'oid_type': 'oid_type',
        'room': 'room',
        'status': 'status',
        'sec_level': 'sec_level',
        'created_at': 'created_at' # Додаємо поле для сортування за датою створення
    }
    
    order_by_field_key = valid_sort_fields.get(sort_by_param_cleaned, 'created_at')

    final_order_by_field = f"-{order_by_field_key}" if actual_sort_order_is_desc else order_by_field_key
    
    # Додаємо вторинне сортування для стабільності
    if order_by_field_key == 'created_at':
        secondary_sort = 'cipher'
    elif order_by_field_key == 'cipher':
        secondary_sort = '-created_at'
    else:
        secondary_sort = '-created_at' # Загальне вторинне сортування

    oid_list_queryset = oid_list_queryset.order_by(final_order_by_field, secondary_sort)

    # --- Пагінація ---
    paginator = Paginator(oid_list_queryset, 25) # 25 ОІД на сторінку
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Дані для фільтрів
    units_for_filter = Unit.objects.all().order_by('code')
    # Передаємо самі choices, а не їх відображення
    oid_type_choices_for_filter = OIDTypeChoices.choices
    oid_status_choices_for_filter = OIDStatusChoices.choices
    sec_level_choices_for_filter = SecLevelChoices.choices
        
    context = {
        'page_title': 'Список Об\'єктів Інформаційної Діяльності (ОІД)',
        'object_list': page_obj, # 'object_list' використовується у вашому шаблоні
        'page_obj': page_obj,    # для пагінації
        # Фільтри
        'units_for_filter': units_for_filter,
        'oid_type_choices_for_filter': oid_type_choices_for_filter,
        'oid_status_choices_for_filter': oid_status_choices_for_filter,
        'sec_level_choices_for_filter': sec_level_choices_for_filter,
        'current_filter_unit_id': current_filter_unit_id,
        'current_filter_oid_type': filter_oid_type,
        'current_filter_status': filter_status,
        'current_filter_sec_level': filter_sec_level,
        'current_search_query': search_query,
        # Сортування
        'current_sort_by': sort_by_param_cleaned, # Чистий параметр сортування
        'current_sort_order_is_desc': actual_sort_order_is_desc, # Поточний напрямок desc (true/false)
    }
    return render(request, 'oids/lists/oid_list.html', context)

def work_request_list_view(request):
    work_request_list_queryset = WorkRequest.objects.select_related(
        'unit', 
        'unit__territorial_management' # Для можливого відображення ТУ
    ).prefetch_related(
        Prefetch('items', queryset=WorkRequestItem.objects.select_related('oid')) 
    )

    # --- Фільтрація ---
    filter_unit_id_str = request.GET.get('filter_unit')
    filter_status = request.GET.get('filter_status')
    filter_date_from_str = request.GET.get('filter_date_from')
    filter_date_to_str = request.GET.get('filter_date_to')
    search_query = request.GET.get('search_query')

    current_filter_unit_id = None
    if filter_unit_id_str and filter_unit_id_str.isdigit():
        current_filter_unit_id = int(filter_unit_id_str)
        work_request_list_queryset = work_request_list_queryset.filter(unit__id=current_filter_unit_id)
    
    if filter_status:
        work_request_list_queryset = work_request_list_queryset.filter(status=filter_status)

    current_filter_date_from = None
    if filter_date_from_str:
        try:
            current_filter_date_from = datetime.strptime(filter_date_from_str, '%Y-%m-%d').date()
            work_request_list_queryset = work_request_list_queryset.filter(incoming_date__gte=current_filter_date_from)
        except ValueError:
            current_filter_date_from = None # Якщо дата невалідна, ігноруємо

    current_filter_date_to = None
    if filter_date_to_str:
        try:
            current_filter_date_to = datetime.strptime(filter_date_to_str, '%Y-%m-%d').date()
            work_request_list_queryset = work_request_list_queryset.filter(incoming_date__lte=current_filter_date_to)
        except ValueError:
            current_filter_date_to = None # Якщо дата невалідна, ігноруємо
            
    if search_query:
        work_request_list_queryset = work_request_list_queryset.filter(
            Q(incoming_number__icontains=search_query) |
            Q(unit__code__icontains=search_query) | # Пошук за кодом ВЧ
            Q(unit__name__icontains=search_query) | # Пошук за назвою ВЧ
            Q(items__oid__cipher__icontains=search_query) # Пошук за шифром ОІД в елементах заявки
        ).distinct() # distinct потрібен через фільтрацію по M2M (items)

    # --- Сортування ---
    sort_by_param = request.GET.get('sort_by', '-incoming_date') # За замовчуванням - новіші заявки
    sort_order_from_request = request.GET.get('sort_order', '') 

    actual_sort_order_is_desc = False
    if sort_by_param.startswith('-'):
        actual_sort_order_is_desc = True
        sort_by_param_cleaned = sort_by_param[1:]
    else:
        sort_by_param_cleaned = sort_by_param
        if sort_order_from_request == 'desc':
            actual_sort_order_is_desc = True
            
    valid_sort_fields = {
        'unit': 'unit__code',
        'number': 'incoming_number',
        'date': 'incoming_date',
        'status': 'status',
    }
    
    order_by_field_key = valid_sort_fields.get(sort_by_param_cleaned, 'incoming_date')
    final_order_by_field = f"-{order_by_field_key}" if actual_sort_order_is_desc else order_by_field_key
    
    # Вторинне сортування
    secondary_sort = '-pk' if order_by_field_key != 'incoming_date' else 'unit__code'

    work_request_list_queryset = work_request_list_queryset.order_by(final_order_by_field, secondary_sort)

    # --- Пагінація ---
    paginator = Paginator(work_request_list_queryset, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    # Дані для фільтрів
    units_for_filter = Unit.objects.all().order_by('code')
    status_choices_for_filter = WorkRequestStatusChoices.choices
        
    context = {
        'page_title': 'Список Заявок на Проведення Робіт',
        'object_list': page_obj,
        'page_obj': page_obj,
        # Фільтри
        'units_for_filter': units_for_filter,
        'status_choices_for_filter': status_choices_for_filter,
        'current_filter_unit_id': current_filter_unit_id,
        'current_filter_status': filter_status,
        'current_filter_date_from': filter_date_from_str, # Передаємо рядок для заповнення поля форми
        'current_filter_date_to': filter_date_to_str,     # Передаємо рядок для заповнення поля форми
        'current_search_query': search_query,
        # Сортування
        'current_sort_by': sort_by_param_cleaned,
        'current_sort_order_is_desc': actual_sort_order_is_desc,
    }
    return render(request, 'oids/lists/work_request_list.html', context)
 

def trip_list_view(request):
    trip_list_queryset = Trip.objects.prefetch_related(
        'units', 
        'oids__unit', # Для доступу до oid.unit.code без додаткових запитів
        'persons', 
        'work_requests'
    )

    # --- Фільтрація ---
    filter_unit_id_str = request.GET.get('filter_unit')
    filter_person_id_str = request.GET.get('filter_person')
    filter_date_from_str = request.GET.get('filter_date_from')
    filter_date_to_str = request.GET.get('filter_date_to')
    search_query = request.GET.get('search_query') # Для мети, шифру ОІД, коду ВЧ

    current_filter_unit_id = None
    if filter_unit_id_str and filter_unit_id_str.isdigit():
        current_filter_unit_id = int(filter_unit_id_str)
        # Фільтруємо відрядження, які мають цю ВЧ у своєму списку units
        trip_list_queryset = trip_list_queryset.filter(units__id=current_filter_unit_id) 
    
    current_filter_person_id = None
    if filter_person_id_str and filter_person_id_str.isdigit():
        current_filter_person_id = int(filter_person_id_str)
        # Фільтруємо відрядження, які мають цю особу у своєму списку persons
        trip_list_queryset = trip_list_queryset.filter(persons__id=current_filter_person_id)

    current_filter_date_from = None
    if filter_date_from_str:
        try:
            current_filter_date_from = datetime.strptime(filter_date_from_str, '%Y-%m-%d').date()
            # Фільтр по даті початку АБО даті закінчення (або перетину діапазону)
            trip_list_queryset = trip_list_queryset.filter(
                Q(start_date__gte=current_filter_date_from) | Q(end_date__gte=current_filter_date_from)
            )
        except ValueError:
            current_filter_date_from = None

    current_filter_date_to = None
    if filter_date_to_str:
        try:
            current_filter_date_to = datetime.strptime(filter_date_to_str, '%Y-%m-%d').date()
            trip_list_queryset = trip_list_queryset.filter(
                Q(start_date__lte=current_filter_date_to) | Q(end_date__lte=current_filter_date_to)
            )
        except ValueError:
            current_filter_date_to = None
            
    if search_query:
        trip_list_queryset = trip_list_queryset.filter(
            Q(purpose__icontains=search_query) |
            Q(units__code__icontains=search_query) |
            Q(oids__cipher__icontains=search_query) |
            Q(persons__full_name__icontains=search_query) |
            Q(work_requests__incoming_number__icontains=search_query)
        ).distinct() # distinct важливий через пошук по M2M

    # --- Сортування ---
    sort_by_param = request.GET.get('sort_by', '-start_date') # За замовчуванням - новіші відрядження
    sort_order_from_request = request.GET.get('sort_order', '') 

    actual_sort_order_is_desc = False
    if sort_by_param.startswith('-'):
        actual_sort_order_is_desc = True
        sort_by_param_cleaned = sort_by_param[1:]
    else:
        sort_by_param_cleaned = sort_by_param
        if sort_order_from_request == 'desc':
            actual_sort_order_is_desc = True
            
    valid_sort_fields = {
        'start_date': 'start_date',
        'end_date': 'end_date',
        'purpose': 'purpose',
        # Сортування за M2M полями (units, oids, persons) напряму через order_by складне.
        # Якщо потрібно, це вимагає анотації або більш складних запитів.
        # Поки що обмежимось прямими полями моделі Trip.
    }
    
    order_by_field_key = valid_sort_fields.get(sort_by_param_cleaned, 'start_date')
    final_order_by_field = f"-{order_by_field_key}" if actual_sort_order_is_desc else order_by_field_key
    
    secondary_sort = '-pk' # Загальне вторинне сортування для стабільності

    trip_list_queryset = trip_list_queryset.order_by(final_order_by_field, secondary_sort).distinct() # distinct тут теж може бути корисним

    # --- Пагінація ---
    paginator = Paginator(trip_list_queryset, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    # Дані для фільтрів
    units_for_filter = Unit.objects.all().order_by('code')
    persons_for_filter = Person.objects.filter(is_active=True).order_by('full_name')
        
    context = {
        'page_title': 'Список Відряджень',
        'object_list': page_obj,
        'page_obj': page_obj,
        # Фільтри
        'units_for_filter': units_for_filter,
        'persons_for_filter': persons_for_filter,
        'current_filter_unit_id': current_filter_unit_id,
        'current_filter_person_id': current_filter_person_id,
        'current_filter_date_from': filter_date_from_str,
        'current_filter_date_to': filter_date_to_str,
        'current_search_query': search_query,
        # Сортування
        'current_sort_by': sort_by_param_cleaned,
        'current_sort_order_is_desc': actual_sort_order_is_desc,
    }
    return render(request, 'oids/lists/trip_list.html', context)

def technical_task_list_view(request):
    task_list_queryset = TechnicalTask.objects.select_related(
        'oid__unit', 
        'oid',
        'reviewed_by'
    )

    # --- Фільтрація ---
    filter_unit_id_str = request.GET.get('filter_unit')
    filter_oid_id_str = request.GET.get('filter_oid')
    filter_review_result = request.GET.get('filter_review_result')
    filter_reviewed_by_id_str = request.GET.get('filter_reviewed_by')
    
    filter_input_date_from_str = request.GET.get('filter_input_date_from')
    filter_input_date_to_str = request.GET.get('filter_input_date_to')
    filter_read_till_date_from_str = request.GET.get('filter_read_till_date_from')
    filter_read_till_date_to_str = request.GET.get('filter_read_till_date_to')
    
    search_query = request.GET.get('search_query')

    current_filter_unit_id = None
    if filter_unit_id_str and filter_unit_id_str.isdigit():
        current_filter_unit_id = int(filter_unit_id_str)
        task_list_queryset = task_list_queryset.filter(oid__unit__id=current_filter_unit_id)

    current_filter_oid_id = None
    if filter_oid_id_str and filter_oid_id_str.isdigit():
        current_filter_oid_id = int(filter_oid_id_str)
        task_list_queryset = task_list_queryset.filter(oid__id=current_filter_oid_id)
    
    if filter_review_result:
        task_list_queryset = task_list_queryset.filter(review_result=filter_review_result)

    current_filter_reviewed_by_id = None
    if filter_reviewed_by_id_str and filter_reviewed_by_id_str.isdigit():
        current_filter_reviewed_by_id = int(filter_reviewed_by_id_str)
        task_list_queryset = task_list_queryset.filter(reviewed_by__id=current_filter_reviewed_by_id)

    # Фільтри по датах
    current_filter_input_date_from = None
    if filter_input_date_from_str:
        try:
            current_filter_input_date_from = datetime.strptime(filter_input_date_from_str, '%Y-%m-%d').date()
            task_list_queryset = task_list_queryset.filter(input_date__gte=current_filter_input_date_from)
        except ValueError:
            current_filter_input_date_from = None

    current_filter_input_date_to = None
    if filter_input_date_to_str:
        try:
            current_filter_input_date_to = datetime.strptime(filter_input_date_to_str, '%Y-%m-%d').date()
            task_list_queryset = task_list_queryset.filter(input_date__lte=current_filter_input_date_to)
        except ValueError:
            current_filter_input_date_to = None
            
    current_filter_read_till_date_from = None
    if filter_read_till_date_from_str:
        try:
            current_filter_read_till_date_from = datetime.strptime(filter_read_till_date_from_str, '%Y-%m-%d').date()
            task_list_queryset = task_list_queryset.filter(read_till_date__gte=current_filter_read_till_date_from) #
        except ValueError:
            current_filter_read_till_date_from = None
            
    current_filter_read_till_date_to = None
    if filter_read_till_date_to_str:
        try:
            current_filter_read_till_date_to = datetime.strptime(filter_read_till_date_to_str, '%Y-%m-%d').date()
            task_list_queryset = task_list_queryset.filter(read_till_date__lte=current_filter_read_till_date_to) #
        except ValueError:
            current_filter_read_till_date_to = None
            
    if search_query:
        task_list_queryset = task_list_queryset.filter(
            Q(input_number__icontains=search_query) |
            Q(oid__cipher__icontains=search_query) |
            Q(oid__full_name__icontains=search_query) |
            Q(note__icontains=search_query)
        ).distinct()

    # --- Сортування ---
    sort_by_param = request.GET.get('sort_by', '-input_date') # За замовчуванням, як у вас було
    sort_order_from_request = request.GET.get('sort_order', '') 

    actual_sort_order_is_desc = False
    if sort_by_param.startswith('-'):
        actual_sort_order_is_desc = True
        sort_by_param_cleaned = sort_by_param[1:]
    else:
        sort_by_param_cleaned = sort_by_param
        if sort_order_from_request == 'desc':
            actual_sort_order_is_desc = True
            
    valid_sort_fields = {
        'oid_loc': 'oid__unit__code', # Сортування за кодом ВЧ, потім можна додати шифр ОІД
        'input_number': 'input_number', #
        'input_date': 'input_date', #
        'read_till_date': 'read_till_date', #
        'review_result': 'review_result', #
        'reviewed_by': 'reviewed_by__full_name',
        'created_at': 'created_at' #
    }
    
    order_by_field_key = valid_sort_fields.get(sort_by_param_cleaned, 'input_date')
    final_order_by_field = f"-{order_by_field_key}" if actual_sort_order_is_desc else order_by_field_key
    
    # Вторинне сортування
    if order_by_field_key == 'input_date':
        secondary_sort = '-created_at' #
    elif order_by_field_key == 'oid__unit__code':
        secondary_sort = 'oid__cipher' # Якщо сортуємо за ВЧ, то потім за шифром ОІД
    else:
        secondary_sort = '-input_date'

    task_list_queryset = task_list_queryset.order_by(final_order_by_field, secondary_sort).distinct()

    # --- Пагінація ---
    paginator = Paginator(task_list_queryset, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    # Дані для фільтрів
    units_for_filter = Unit.objects.all().order_by('code')
    # Якщо ОІДів дуже багато, цей список може бути великим. 
    # Розгляньте можливість динамічного завантаження ОІДів залежно від обраної ВЧ у фільтрі, якщо це стане проблемою.
    oids_for_filter = OID.objects.select_related('unit').all().order_by('unit__code', 'cipher') 
    review_result_choices_for_filter = DocumentReviewResultChoices.choices #
    # Фільтруємо осіб, які справді щось розглядали, щоб список не був занадто великим
    persons_for_filter = Person.objects.filter(reviewed_technical_tasks__isnull=False).distinct().order_by('full_name')
        
    context = {
        'page_title': 'Список Технічних Завдань',
        'object_list': page_obj,
        'page_obj': page_obj,
        # Фільтри
        'units_for_filter': units_for_filter,
        'oids_for_filter': oids_for_filter,
        'review_result_choices_for_filter': review_result_choices_for_filter,
        'persons_for_filter': persons_for_filter,
        'current_filter_unit_id': current_filter_unit_id,
        'current_filter_oid_id': current_filter_oid_id,
        'current_filter_review_result': filter_review_result,
        'current_filter_reviewed_by_id': current_filter_reviewed_by_id,
        'current_filter_input_date_from': filter_input_date_from_str,
        'current_filter_input_date_to': filter_input_date_to_str,
        'current_filter_read_till_date_from': filter_read_till_date_from_str,
        'current_filter_read_till_date_to': filter_read_till_date_to_str,
        'current_search_query': search_query,
        # Сортування
        'current_sort_by': sort_by_param_cleaned,
        'current_sort_order_is_desc': actual_sort_order_is_desc,
    }
    return render(request, 'oids/lists/technical_task_list.html', context)

def attestation_registration_list_view(request):
    registration_list_queryset = AttestationRegistration.objects.prefetch_related(
        'units',  # ManyToMany зв'язок з Unit
        Prefetch('attestation_items', queryset=AttestationItem.objects.select_related('oid__unit', 'document')) # Для доступу до ОІД та документів
    ).order_by('-process_date') # Сортуємо за датою відправки, новіші зверху

    paginator = Paginator(registration_list_queryset, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    context = {
        'page_title': 'Список Реєстрацій Актів Атестації',
        'object_list': page_obj,
        'page_obj': page_obj
    }
    return render(request, 'oids/lists/attestation_registration_list.html', context)

def attestation_response_list_view(request):
    response_list_queryset = AttestationResponse.objects.select_related(
        'registration' # Для доступу до даних оригінальної реєстрації
    ).order_by('-registered_date', '-recorded_date') # Сортуємо за датою реєстрації, потім за датою внесення

    paginator = Paginator(response_list_queryset, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    context = {
        'page_title': 'Список Відповідей на Реєстрацію Актів Атестації',
        'object_list': page_obj,
        'page_obj': page_obj
    }
    return render(request, 'oids/lists/attestation_response_list.html', context)

def trip_result_for_unit_list_view(request):
    result_list_queryset = TripResultForUnit.objects.select_related(
        'trip' # Якщо потрібно бачити деталі самого відрядження
    ).prefetch_related(
        'units', # ВЧ, куди відправлено
        Prefetch('oids', queryset=OID.objects.select_related('unit')), # ОІДи, що стосуються результату
        Prefetch('documents', queryset=Document.objects.select_related('document_type')) # Документи, що відправлені
    ).order_by('-process_date') # Сортуємо за датою відправки до частини

    paginator = Paginator(result_list_queryset, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    context = {
        'page_title': 'Список Результатів Відряджень (відправка до ВЧ)',
        'object_list': page_obj,
        'page_obj': page_obj
    }
    return render(request, 'oids/lists/trip_result_for_unit_list.html', context)

def oid_status_change_list_view(request):
    status_change_list_queryset = OIDStatusChange.objects.select_related(
        'oid__unit', 
        'oid',
        'initiating_document__document_type', 
        'changed_by' 
    )

    # --- Фільтрація ---
    filter_unit_id_str = request.GET.get('filter_unit')
    filter_oid_id_str = request.GET.get('filter_oid')
    filter_old_status = request.GET.get('filter_old_status')
    filter_new_status = request.GET.get('filter_new_status')
    filter_changed_by_id_str = request.GET.get('filter_changed_by')
    filter_date_from_str = request.GET.get('filter_date_from')
    filter_date_to_str = request.GET.get('filter_date_to')
    search_query = request.GET.get('search_query') # Для ОІД, причини, документа

    current_filter_unit_id = None
    if filter_unit_id_str and filter_unit_id_str.isdigit():
        current_filter_unit_id = int(filter_unit_id_str)
        status_change_list_queryset = status_change_list_queryset.filter(oid__unit__id=current_filter_unit_id)

    current_filter_oid_id = None
    if filter_oid_id_str and filter_oid_id_str.isdigit():
        current_filter_oid_id = int(filter_oid_id_str)
        status_change_list_queryset = status_change_list_queryset.filter(oid__id=current_filter_oid_id)
    
    if filter_old_status:
        status_change_list_queryset = status_change_list_queryset.filter(old_status=filter_old_status)
    
    if filter_new_status:
        status_change_list_queryset = status_change_list_queryset.filter(new_status=filter_new_status)

    current_filter_changed_by_id = None
    if filter_changed_by_id_str and filter_changed_by_id_str.isdigit():
        current_filter_changed_by_id = int(filter_changed_by_id_str)
        status_change_list_queryset = status_change_list_queryset.filter(changed_by__id=current_filter_changed_by_id)

    current_filter_date_from = None
    if filter_date_from_str:
        try:
            current_filter_date_from = datetime.strptime(filter_date_from_str, '%Y-%m-%d').date()
            status_change_list_queryset = status_change_list_queryset.filter(changed_at__date__gte=current_filter_date_from)
        except ValueError:
            current_filter_date_from = None

    current_filter_date_to = None
    if filter_date_to_str:
        try:
            current_filter_date_to = datetime.strptime(filter_date_to_str, '%Y-%m-%d').date()
            status_change_list_queryset = status_change_list_queryset.filter(changed_at__date__lte=current_filter_date_to)
        except ValueError:
            current_filter_date_to = None
            
    if search_query:
        status_change_list_queryset = status_change_list_queryset.filter(
            Q(oid__cipher__icontains=search_query) |
            Q(oid__unit__code__icontains=search_query) |
            Q(reason__icontains=search_query) |
            Q(initiating_document__document_number__icontains=search_query) |
            Q(initiating_document__document_type__name__icontains=search_query)
        ).distinct()

    # --- Сортування ---
    sort_by_param = request.GET.get('sort_by', '-changed_at') # За замовчуванням
    sort_order_from_request = request.GET.get('sort_order', '') 

    actual_sort_order_is_desc = False
    if sort_by_param.startswith('-'):
        actual_sort_order_is_desc = True
        sort_by_param_cleaned = sort_by_param[1:]
    else:
        sort_by_param_cleaned = sort_by_param
        if sort_order_from_request == 'desc':
            actual_sort_order_is_desc = True
            
    valid_sort_fields = {
        'oid_loc': 'oid__unit__code', 
        'changed_at': 'changed_at',
        'old_status': 'old_status',
        'new_status': 'new_status',
        'reason': 'reason', # Сортування за причиною може бути менш корисним
        'document': 'initiating_document__document_number', # Або initiating_document__document_type__name
        'changed_by': 'changed_by__full_name',
    }
    
    order_by_field_key = valid_sort_fields.get(sort_by_param_cleaned, 'changed_at')
    final_order_by_field = f"-{order_by_field_key}" if actual_sort_order_is_desc else order_by_field_key
    
    secondary_sort = '-pk' if order_by_field_key != 'changed_at' else 'oid__cipher'

    status_change_list_queryset = status_change_list_queryset.order_by(final_order_by_field, secondary_sort).distinct()

    # --- Пагінація ---
    paginator = Paginator(status_change_list_queryset, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
        
    # Дані для фільтрів
    units_for_filter = Unit.objects.all().order_by('code')
    oids_for_filter = OID.objects.select_related('unit').all().order_by('unit__code', 'cipher')
    # Припускаємо, що old_status та new_status використовують ті ж choices, що й статус ОІД
    status_choices_for_filter = OIDStatusChoices.choices 
    persons_for_filter = Person.objects.filter(oid_status_changes__isnull=False).distinct().order_by('full_name')
        
    context = {
        'page_title': 'Історія Змін Статусу ОІД',
        'object_list': page_obj,
        'page_obj': page_obj,
        # Фільтри
        'units_for_filter': units_for_filter,
        'oids_for_filter': oids_for_filter,
        'status_choices_for_filter': status_choices_for_filter, # Однаковий для old_status та new_status
        'persons_for_filter': persons_for_filter,
        'current_filter_unit_id': current_filter_unit_id,
        'current_filter_oid_id': current_filter_oid_id,
        'current_filter_old_status': filter_old_status,
        'current_filter_new_status': filter_new_status,
        'current_filter_changed_by_id': current_filter_changed_by_id,
        'current_filter_date_from': filter_date_from_str,
        'current_filter_date_to': filter_date_to_str,
        'current_search_query': search_query,
        # Сортування
        'current_sort_by': sort_by_param_cleaned,
        'current_sort_order_is_desc': actual_sort_order_is_desc,
    }
    return render(request, 'oids/lists/oid_status_change_list.html', context)

def ajax_create_oid_view(request):
    if request.method == 'POST':
        # Якщо ВЧ передається з форми заявки для попереднього заповнення
        initial_data = {}
        unit_id_from_request_form = request.POST.get('unit_for_new_oid') # Це поле може передаватися з JS
        if unit_id_from_request_form:
            initial_data['unit'] = unit_id_from_request_form
        
        form = OIDForm(request.POST, initial=initial_data) # Використовуємо OIDForm
        if form.is_valid():
            oid = form.save()
            return JsonResponse({
                'status': 'success',
                'message': f'ОІД "{oid.cipher}" успішно створено!',
                'oid_id': oid.id,
                'oid_cipher': oid.cipher,
                'oid_name': str(oid) # Використовуємо __str__ моделі OID
            })
        else:
            # Збираємо помилки валідації для передачі на фронтенд
            errors = {}
            for field, field_errors in form.errors.items():
                errors[field] = [str(e) for e in field_errors]
            return JsonResponse({'status': 'error', 'errors': errors}, status=400)
    
    # Для GET запиту (якщо модальне вікно завантажує форму через AJAX)
    # або якщо це окрема сторінка
    unit_id_param = request.GET.get('unit_id')
    form = OIDForm(initial={'unit': unit_id_param} if unit_id_param else None)
    
    # Якщо ти хочеш рендерити форму на сервері для модального вікна (менш типово для AJAX)
    # return render(request, 'oids/partials/create_oid_form_content.html', {'oid_form': form})
    
    # Зазвичай, якщо модальне вікно вже має HTML структуру форми, цей GET не потрібен,
    # або він може повертати порожню форму як HTML для вставки.
    # Для чистого AJAX-створення GET-обробник може бути непотрібним, якщо форма статична в модалці.
    return JsonResponse({'error': 'Only POST requests are allowed for creating OID via AJAX here'}, status=405)
