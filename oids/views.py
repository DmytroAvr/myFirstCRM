# oids/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Max
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

# Імпортуємо наші моделі
from .models import (
    TerritorialManagement, Unit, OID, WorkRequest, WorkRequestItem,
    Document, DocumentType, Trip, Person, OIDStatusChoices, WorkRequestStatusChoices,
    WorkTypeChoices, TechnicalTask
)

# --- Утиліти та Допоміжні Функції (можна винести в окремий файл, наприклад, utils.py) ---

def get_last_ik_expiration_date(oid):
    """
    Повертає дату завершення дії останнього Висновку ІК для ОІД.
    """
    try:
        # Шукаємо останній документ типу "Висновок ІК" для даного ОІД
        # Припускаємо, що DocumentType з назвою "Висновок ІК" існує і має work_type='ІК'
        ik_conclusion_doc_type = DocumentType.objects.get(
            name__icontains='Висновок', # 'Висновок ІК' або 'Висновок'
            work_type=WorkTypeChoices.IK
        )
        last_ik_document = Document.objects.filter(
            oid=oid,
            document_type=ik_conclusion_doc_type,
            expiration_date__isnull=False # Перевіряємо, що є термін дії
        ).order_by('-work_date').first() # Беремо найновіший за датою проведення робіт

        return last_ik_document.expiration_date if last_ik_document else None
    except DocumentType.DoesNotExist:
        # Якщо тип документа "Висновок ІК" не знайдено в базі даних, повертаємо None
        return None
    except Exception as e:
        print(f"Помилка при отриманні терміну дії ІК для ОІД {oid.cipher}: {e}")
        return None

# --- Представлення (Views) ---

def main_dashboard(request):
    """
    Головна сторінка з трьома стовпчиками та кнопками керування.
    """
    # Панель керування зверху (посилання на форми)
    add_request_url = reverse('add_work_request') # Потрібно буде створити URL
    plan_trip_url = reverse('plan_trip')         # Потрібно буде створити URL
    add_document_processing_url = reverse('add_document_processing') # Потрібно буде створити URL

    # 1. Колонка: Територіальні управління
    territorial_managements = TerritorialManagement.objects.all().order_by('name')
    
    selected_tm_id = request.GET.get('tm')
    selected_unit_id = request.GET.get('unit')

    # 2. Колонка: Військові частини
    units = Unit.objects.all().order_by('name')
    if selected_tm_id:
        # Фільтруємо частини за обраним ТУ
        units = units.filter(territorial_management__id=selected_tm_id)
    
    # 3. Колонка: ОІД
    oids_creating = OID.objects.none() # ОІД, які створюються
    oids_active = OID.objects.none()   # Діючі ОІД
    oids_cancelled = OID.objects.none() # Скасовані ОІД

    if selected_unit_id:
        current_oids = OID.objects.filter(unit__id=selected_unit_id).order_by('cipher')

        # ОІД, які створюються (наявна заявка)
        oids_creating = current_oids.filter(
            status__in=[
                OIDStatusChoices.NEW,
                OIDStatusChoices.RECEIVED_REQUEST,
                OIDStatusChoices.RECEIVED_TZ
            ]
        ).prefetch_related('work_request_items__request') # Оптимізація запитів

        # Діючі ОІД
        oids_active = current_oids.filter(status=OIDStatusChoices.ACTIVE)
        
        # Скасовані ОІД
        oids_cancelled = current_oids.filter(
            status__in=[
                OIDStatusChoices.CANCELED,
                OIDStatusChoices.TERMINATED
            ]
        )
    elif selected_tm_id:
        # Якщо обрано лише ТУ, показуємо ОІД з усіх частин цього ТУ
        current_oids = OID.objects.filter(unit__territorial_management__id=selected_tm_id).order_by('cipher')
        oids_creating = current_oids.filter(
            status__in=[
                OIDStatusChoices.NEW,
                OIDStatusChoices.RECEIVED_REQUEST,
                OIDStatusChoices.RECEIVED_TZ
            ]
        ).prefetch_related('work_request_items__request')
        oids_active = current_oids.filter(status=OIDStatusChoices.ACTIVE)
        oids_cancelled = current_oids.filter(
            status__in=[
                OIDStatusChoices.CANCELED,
                OIDStatusChoices.TERMINATED
            ]
        )
    else:
        # Якщо нічого не обрано, показуємо всі ОІД
        current_oids = OID.objects.all().order_by('cipher')
        oids_creating = current_oids.filter(
            status__in=[
                OIDStatusChoices.NEW,
                OIDStatusChoices.RECEIVED_REQUEST,
                OIDStatusChoices.RECEIVED_TZ
            ]
        ).prefetch_related('work_request_items__request')
        oids_active = current_oids.filter(status=OIDStatusChoices.ACTIVE)
        oids_cancelled = current_oids.filter(
            status__in=[
                OIDStatusChoices.CANCELED,
                OIDStatusChoices.TERMINATED
            ]
        )

    # Для діючих ОІД потрібно отримати термін дії ІК
    for oid in oids_active:
        oid.ik_expiration_date = get_last_ik_expiration_date(oid)


    context = {
        'add_request_url': add_request_url,
        'plan_trip_url': plan_trip_url,
        'add_document_processing_url': add_document_processing_url,

        'territorial_managements': territorial_managements,
        'selected_tm_id': int(selected_tm_id) if selected_tm_id else None,
        
        'units': units,
        'selected_unit_id': int(selected_unit_id) if selected_unit_id else None,
        
        'oids_creating': oids_creating,
        'oids_active': oids_active,
        'oids_cancelled': oids_cancelled,
    }

    return render(request, 'oids/main_dashboard.html', context)


def oid_detail_view(request, oid_id):
    """
    Відображає детальну інформацію про конкретний ОІД.
    """
    oid = get_object_or_404(OID.objects.select_related('unit__territorial_management'), pk=oid_id)

    # 1. Історія змін статусу
    status_changes = oid.status_changes.select_related('initiating_document', 'changed_by').order_by('-changed_at')

    # 2. Пов'язані заявки та елементи заявок
    # Отримуємо всі унікальні заявки, пов'язані з цим ОІД через WorkRequestItem
    # Якщо WorkRequestItem має related_name='items' для WorkRequest, то:
    work_requests_for_oid = WorkRequest.objects.filter(items__oid=oid).distinct().order_by('-incoming_date')
    
    # Або можна отримати всі WorkRequestItem для даного ОІД:
    work_request_items = oid.work_request_items.select_related('request').order_by('-request__incoming_date')

    # 3. Технічні завдання
    technical_tasks = oid.technical_tasks.select_related('reviewed_by').order_by('-input_date')

    # 4. Опрацьовані документи
    documents = oid.documents.select_related('document_type', 'author', 'work_request_item').order_by('-process_date')

    # 5. Історія відряджень (які включали цей ОІД)
    trips_for_oid = oid.trips.prefetch_related('units', 'persons', 'work_requests').order_by('-start_date')

    # 6. Реєстрації атестацій (якщо ОІД був частиною зареєстрованого акту атестації)
    attestation_registrations = AttestationRegistration.objects.filter(attestation_items__oid=oid).distinct().order_by('-process_date')
    
    # Можна також додати останній термін дії атестації та ІК тут для швидкого доступу
    last_attestation_expiration = None
    last_ik_expiration = get_last_ik_expiration_date(oid)

    try:
        attestation_doc_type = DocumentType.objects.get(
            name__icontains='Акт атестації', 
            work_type=WorkTypeChoices.ATTESTATION
        )
        last_attestation_doc = Document.objects.filter(
            oid=oid,
            document_type=attestation_doc_type,
            expiration_date__isnull=False
        ).order_by('-work_date').first()
        if last_attestation_doc:
            last_attestation_expiration = last_attestation_doc.expiration_date
    except DocumentType.DoesNotExist:
        pass


    context = {
        'oid': oid,
        'status_changes': status_changes,
        'work_requests_for_oid': work_requests_for_oid, # Унікальні заявки
        'work_request_items': work_request_items,       # Елементи заявок
        'technical_tasks': technical_tasks,
        'documents': documents,
        'trips_for_oid': trips_for_oid,
        'attestation_registrations': attestation_registrations,
        'last_attestation_expiration': last_attestation_expiration,
        'last_ik_expiration': last_ik_expiration,
    }
    return render(request, 'oids/oid_detail.html', context)


# --- Приклад placeholder-ів для форм ---
# Ці представлення будуть обробляти POST-запити від форм.
# Для простоти, тут лише редирект, але в реальному проекті тут буде логіка обробки форм.

def add_work_request(request):
    if request.method == 'POST':
        # Логіка обробки форми додавання заявки
        # ...
        return redirect('main_dashboard') # Після успішного додавання повертаємося на головну

    # Відображення форми
    return render(request, 'oids/forms/add_work_request_form.html', {})

def plan_trip(request):
    if request.method == 'POST':
        # Логіка обробки форми планування відрядження
        # ...
        return redirect('main_dashboard')

    # Відображення форми
    return render(request, 'oids/forms/plan_trip_form.html', {})

def add_document_processing(request):
    if request.method == 'POST':
        # Логіка обробки форми додавання опрацювання документів
        # ...
        return redirect('main_dashboard')

    # Відображення форми
    return render(request, 'oids/forms/add_document_processing_form.html', {})


# oids/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Max
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

# Імпортуємо наші моделі та форми
from .models import (
    TerritorialManagement, Unit, OID, WorkRequest, WorkRequestItem,
    Document, DocumentType, Trip, Person, OIDStatusChoices, WorkRequestStatusChoices,
    WorkTypeChoices, TechnicalTask
)
from .forms import WorkRequestForm, TripForm, DocumentForm # Імпортуємо форми

# --- Утиліти та Допоміжні Функції (можна винести в окремий файл, наприклад, utils.py) ---

def get_last_ik_expiration_date(oid):
    """
    Повертає дату завершення дії останнього Висновку ІК для ОІД.
    """
    try:
        ik_conclusion_doc_type = DocumentType.objects.get(
            name__icontains='Висновок',
            work_type=WorkTypeChoices.IK
        )
        last_ik_document = Document.objects.filter(
            oid=oid,
            document_type=ik_conclusion_doc_type,
            expiration_date__isnull=False
        ).order_by('-work_date').first()

        return last_ik_document.expiration_date if last_ik_document else None
    except DocumentType.DoesNotExist:
        return None
    except Exception as e:
        print(f"Помилка при отриманні терміну дії ІК для ОІД {oid.cipher}: {e}")
        return None

# --- Представлення (Views) ---

def main_dashboard(request):
    """
    Головна сторінка з трьома стовпчиками та кнопками керування.
    """
    # Панель керування зверху (посилання на форми)
    add_request_url = reverse('add_work_request')
    plan_trip_url = reverse('plan_trip')
    add_document_processing_url = reverse('add_document_processing')

    # 1. Колонка: Територіальні управління
    territorial_managements = TerritorialManagement.objects.all().order_by('name')
    
    selected_tm_id = request.GET.get('tm')
    selected_unit_id = request.GET.get('unit')

    # 2. Колонка: Військові частини
    units = Unit.objects.all().order_by('name')
    if selected_tm_id:
        units = units.filter(territorial_management__id=selected_tm_id)
    
    # 3. Колонка: ОІД
    oids_creating = OID.objects.none()
    oids_active = OID.objects.none()
    oids_cancelled = OID.objects.none()

    current_oids_queryset = OID.objects.all()

    if selected_unit_id:
        current_oids_queryset = current_oids_queryset.filter(unit__id=selected_unit_id)
    elif selected_tm_id:
        current_oids_queryset = current_oids_queryset.filter(unit__territorial_management__id=selected_tm_id)

    # Фільтруємо ОІД за статусами
    oids_creating = current_oids_queryset.filter(
        status__in=[
            OIDStatusChoices.NEW,
            OIDStatusChoices.RECEIVED_REQUEST,
            OIDStatusChoices.RECEIVED_TZ
        ]
    ).select_related('unit').prefetch_related('work_request_items__request') # Оптимізація запитів

    oids_active = current_oids_queryset.filter(status=OIDStatusChoices.ACTIVE).select_related('unit')
    
    oids_cancelled = current_oids_queryset.filter(
        status__in=[
            OIDStatusChoices.CANCELED,
            OIDStatusChoices.TERMINATED
        ]
    ).select_related('unit')

    # Для діючих ОІД потрібно отримати термін дії ІК
    for oid in oids_active:
        oid.ik_expiration_date = get_last_ik_expiration_date(oid)

    context = {
        'add_request_url': add_request_url,
        'plan_trip_url': plan_trip_url,
        'add_document_processing_url': add_document_processing_url,

        'territorial_managements': territorial_managements,
        'selected_tm_id': int(selected_tm_id) if selected_tm_id else None,
        
        'units': units,
        'selected_unit_id': int(selected_unit_id) if selected_unit_id else None,
        
        'oids_creating': oids_creating,
        'oids_active': oids_active,
        'oids_cancelled': oids_cancelled,
    }

    return render(request, 'oids/main_dashboard.html', context)


def oid_detail_view(request, oid_id):
    """
    Відображає детальну інформацію про конкретний ОІД.
    """
    oid = get_object_or_404(OID.objects.select_related('unit__territorial_management'), pk=oid_id)

    status_changes = oid.status_changes.select_related('initiating_document', 'changed_by').order_by('-changed_at')
    work_requests_for_oid = WorkRequest.objects.filter(items__oid=oid).distinct().order_by('-incoming_date')
    work_request_items = oid.work_request_items.select_related('request').order_by('-request__incoming_date')
    technical_tasks = oid.technical_tasks.select_related('reviewed_by').order_by('-input_date')
    documents = oid.documents.select_related('document_type', 'author', 'work_request_item').order_by('-process_date')
    trips_for_oid = oid.trips.prefetch_related('units', 'persons', 'work_requests').order_by('-start_date')
    attestation_registrations = AttestationRegistration.objects.filter(attestation_items__oid=oid).distinct().order_by('-process_date')
    
    last_attestation_expiration = None
    last_ik_expiration = get_last_ik_expiration_date(oid)

    try:
        attestation_doc_type = DocumentType.objects.get(
            name__icontains='Акт атестації', 
            work_type=WorkTypeChoices.ATTESTATION
        )
        last_attestation_doc = Document.objects.filter(
            oid=oid,
            document_type=attestation_doc_type,
            expiration_date__isnull=False
        ).order_by('-work_date').first()
        if last_attestation_doc:
            last_attestation_expiration = last_attestation_doc.expiration_date
    except DocumentType.DoesNotExist:
        pass


    context = {
        'oid': oid,
        'status_changes': status_changes,
        'work_requests_for_oid': work_requests_for_oid,
        'work_request_items': work_request_items,
        'technical_tasks': technical_tasks,
        'documents': documents,
        'trips_for_oid': trips_for_oid,
        'attestation_registrations': attestation_registrations,
        'last_attestation_expiration': last_attestation_expiration,
        'last_ik_expiration': last_ik_expiration,
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