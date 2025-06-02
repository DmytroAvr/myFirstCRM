# C:\myFirstCRM\oids\views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Document, Unit, OID, OIDStatusChange, WorkRequest, DocumentType, WorkRequestItem, Trip, Person, TechnicalTask
from .forms import DocumentForm, DocumentHeaderForm, DocumentFormSet, requestForm, requestHeaderForm, requestFormSet, requestItemFormSet, requestItemForm, OidCreateForm, AttestationRegistrationForm, TripResultForUnitForm, TechnicalTaskForm, OIDStatusChangeForm, TripForm
from django.http import JsonResponse
import traceback        #check
from django.contrib import messages
from django.views.decorators.http import require_POST, require_GET
from django.db.models import Q
from django.apps import apps  

def home_view(request):
    return render(request, 'home.html')

def load_oids(request):
    try:
        unit_id = request.GET.get('unit')
        oids = OID.objects.filter(unit_id=unit_id).exclude(status='скасовано').order_by('name')
        data = [{'id': oid.id, 'name': oid.name} for oid in oids]
 
        return JsonResponse(list(oids.values('id', 'name')), safe=False)
        # return JsonResponse(data, safe=False)  #proposition for request
    except Exception as e:
        traceback.print_exc()  # ← виведе помилку у консоль VSCode
        return JsonResponse({'error': str(e)}, status=500)

def load_oids_for_unit(request):
    unit_id = request.GET.get('unit')
    oids = OID.objects.filter(unit_id=unit_id).exclude(status='скасовано').order_by('name')
    return JsonResponse(list(oids.values('id', 'name')), safe=False)

def load_oids_for_units(request):
    unit_ids = request.GET.getlist('units[]')
    oids = OID.objects.filter(unit__id__in=unit_ids).exclude(status="скасовано").order_by('name')
    return JsonResponse(list(oids.values('id', 'name')), safe=False)

def get_oid_status(request):
    oid_id = request.GET.get('oid_id')
    try:
        oid = OID.objects.get(id=oid_id)
        return JsonResponse({'status': oid.status})
    except OID.DoesNotExist:
        return JsonResponse({'status': ''})
    
def load_documents_for_oids(request):
    oid_ids = request.GET.getlist('oids[]')
    documents = Document.objects.filter(oid__id__in=oid_ids).order_by('document_type__name', 'document_number')
    return JsonResponse(list(documents.values('id', 'document_type__name', 'document_number')), safe=False)

# один unit дає багато ОІД
def get_oids_by_unit(request):
    unit_id = request.GET.get('unit_id')
    if not unit_id:
        return JsonResponse([], safe=False)

    try:
        unit_id = int(unit_id)
    except ValueError:
        return JsonResponse([], safe=False)

    oids = OID.objects.filter(unit_id=unit_id).values('id', 'name')
    return JsonResponse(list(oids), safe=False)

# багато units дає багато ОІДs
def get_oids_by_units(request):
    unit_ids = request.GET.get('unit_ids')  # приклад: "1,2,3"

    if not unit_ids:
        return JsonResponse([], safe=False)

    ids = [int(i) for i in unit_ids.split(',') if i.isdigit()]
    oids = OID.objects.filter(unit_id__in=ids).values('id', 'name')
    return JsonResponse(list(oids), safe=False)

# всі заявки на 1 ОІД
def get_requests_by_oid(request):
    oid_id = request.GET.get('oid_id')
    if not oid_id:
        return JsonResponse([], safe=False)

    # Знаходимо заявки, пов'язані з OID
    work_requests = WorkRequest.objects.filter(items__oid_id=oid_id).distinct()
    data = [
        {
            'id': wr.id,
            'incoming_number': wr.incoming_number,
            'incoming_date': wr.incoming_date.strftime('%Y-%m-%d') if wr.incoming_date else None # Додав перевірку на None
        }
        for wr in work_requests
    ]
    return JsonResponse(data, safe=False)

# всі заявки на БАГАТо ОІД
def get_requests_by_oids(request):
    oid_ids_list = request.GET.getlist('oid_ids') # Використовуйте getlist для отримання всіх значень

    if not oid_ids_list:
        return JsonResponse([], safe=False)

    ids = [int(i) for i in oid_ids_list if i.isdigit()] # Тепер ids буде списком ID
    work_requests = WorkRequest.objects.filter(items__oid_id__in=ids).distinct()
    data = [
        {
            'id': wr.id,
            'incoming_number': wr.incoming_number,
            'incoming_date': wr.incoming_date.strftime('%Y-%m-%d') if wr.incoming_date else None # Додав перевірку на None
        }
        for wr in work_requests
    ]
    return JsonResponse(data, safe=False)

# додав gemeni
def get_work_request_details(request):
    request_id = request.GET.get('request_id')
    if not request_id:
        return JsonResponse({'error': 'Request ID is required'}, status=400)
    try:
        work_request = WorkRequest.objects.get(pk=request_id)
        # Припускаємо, що WorkRequest пов'язаний з одним OID (наприклад, через ForeignKey)
        # або ви обираєте перший OID, якщо WorkRequest має ManyToMany з OID.
        oid_id = None
        if hasattr(work_request, 'oid') and work_request.oid: # Якщо WorkRequest має ForeignKey до OID
            oid_id = work_request.oid.id
        elif work_request.oids.exists(): # Якщо WorkRequest має ManyToMany до OID
            oid_id = work_request.oids.first().id # Візьмемо перший OID, якщо їх кілька

        unit_id = None
        if oid_id:
            oid = OID.objects.get(pk=oid_id)
            unit_id = oid.unit.id

        return JsonResponse({'oid_id': oid_id, 'unit_id': unit_id})
    except WorkRequest.DoesNotExist:
        return JsonResponse({'error': 'Work Request not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def load_technical_tasks_for_oid(request):
    oid_id = request.GET.get('oid_id')
    tasks = TechnicalTask.objects.filter(oid_id=oid_id).order_by('input_date')
    data = [{'id': task.id, 'input_number': task.input_number, 'input_date': task.input_date.strftime('%Y-%m-%d')} for task in tasks]
    return JsonResponse(data, safe=False)


# C:\myFirstCRM\oids\views.py
def document_done(request):
    if request.method == 'POST':
        header_form = DocumentHeaderForm(request.POST)
        formset = DocumentFormSet(request.POST)

        if header_form.is_valid() and formset.is_valid():
            unit = header_form.cleaned_data['unit']
            oid = header_form.cleaned_data['oid']
            work_type = header_form.cleaned_data['work_type']
            work_date = header_form.cleaned_data['work_date']
            author = header_form.cleaned_data['author']
            process_date = header_form.cleaned_data['process_date']
            
            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    doc = form.save(commit=False)
                    doc.unit = unit
                    doc.oid = oid
                    doc.work_type = work_type
                    doc.work_date = work_date
                    doc.author = author
                    doc.process_date = process_date
                    doc.save()


                messages.success(request, "Документи успішно додано!")
            return redirect('document_done')
    else:
        header_form = DocumentHeaderForm()
        formset = DocumentFormSet(queryset=Document.objects.none())

    return render(request, 'oids/document_done.html', {
        'header_form': header_form,
        'formset': formset
    })

# C:\myFirstCRM\oids\views.py
def work_request(request):
    if request.method == 'POST':
        header_form = requestHeaderForm(request.POST)
        formset = requestItemFormSet(request.POST)

        if header_form.is_valid() and formset.is_valid():
            work_request = header_form.save()

            for form in formset:
                if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                    item = form.save(commit=False)
                    item.request = work_request
                    item.save() 
            
            messages.success(request, "Заявка успішно збережена!")
            return redirect('work_request')  # або інша сторінка
    else:
        header_form = requestHeaderForm()
        formset = requestItemFormSet(queryset=WorkRequestItem.objects.none())

    return render(request, 'oids/work_request.html', {
        'header_form': header_form,
        'formset': formset
    })

def work_request_list(request):
    work_requests = WorkRequest.objects.prefetch_related('items__oid', 'unit').all()
    return render(request, 'views/work_request_list.html', {'work_requests': work_requests})


# aside for request 
@require_POST
def create_oid_ajax(request):
    form = OidCreateForm(request.POST)
    unit_id = request.POST.get('unit_id')

    if not unit_id:
        return JsonResponse({'success': False, 'errors': {'unit_id': ['Unit ID не передано']}}, status=400)

    if form.is_valid():
        oid = form.save(commit=False)		
        try:
            
            unit = Unit.objects.get(id=unit_id)
            oid.unit = unit
            oid.save()
            return JsonResponse({
				'status': 'success',
				'message': f'ОІД "{oid.cipher}" успішно створено!',
				'oid_id': oid.id,
				'oid_cipher': oid.cipher,
				'oid_name': str(oid), 
				'unit_id': oid.unit_id 
			})
            # 
			# return JsonResponse({'success': True, 'oid': {'id': oid.id, 'name': oid.name}})
        except Unit.DoesNotExist:
            return JsonResponse({'success': False, 'errors': {'unit': ['Unit не знайдено']}}, status=400)
    else:
        return JsonResponse({'success': False, 'errors': form.errors}, status=400)
    
# додавання документів

def send_doc_cip(request):
    if request.method == 'POST':
        form = AttestationRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Інформація успішно збережена!")
            return redirect('send_doc_cip')  # або інша сторінка
    else:
        form = AttestationRegistrationForm()
    return render(request, 'send_doc_cip.html', {'form': form})
#    

def send_doc_unit(request):
    if request.method == 'POST':
        form = TripResultForUnitForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Інформація успішно збережена!")
            return redirect('send_doc_unit')  # або інша сторінка
            # return redirect('trip_result_list')  # або інша сторінка
    else:
        form = TripResultForUnitForm() 
    return render(request, 'send_doc_unit.html', {'form': form})

# def trip_result_list(request):
#     results = TripResult.objects.all()
#     return render(request, 'oids/trip_result_list.html', {'results': results})

# Технічне завдання

def create_oid(request):
    if request.method == 'POST':
        form = OIDForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('technical_task_form')  # або назад до TechnicalTask
    else:
        form = OIDForm()
    return render(request, 'oids/oid_form.html', {'form': form})

def change_oid_status(request):
    if request.method == 'POST':
        form = OIDStatusChangeForm(request.POST)
        if form.is_valid():
            oid = form.cleaned_data['oid']
            instance = form.save(commit=False)
            instance.old_status = oid.status  # автоматично вставляємо поточний статус
            instance.save()

            # оновлюємо сам OID
            oid.status = form.cleaned_data['new_status']
            oid.save()

            return redirect('oid_status_change')
    else:
        form = OIDStatusChangeForm()
    return render(request, 'oids/oid_status_change_form.html', {'form': form})


def trip_create_view(request):
    units = Unit.objects.all()
    oids = OID.objects.all()
    work_requests = WorkRequest.objects.all()
    persons = Person.objects.all()

    if request.method == 'POST':
        form = TripForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Відрядження успішно створено!")
            return redirect('trip-create')  # або на іншу сторінку
        else:
            form = TripForm()

    return render(request, 'trip_create.html', {
        'units': units,
        'oids': oids,
        'work_requests': work_requests,
        'persons': persons,
        'selected_units': [],  # при редагуванні — передай відповідні ID
        'selected_oids': [],
        'selected_work_requests': [],
        'selected_persons': [],
        'start_date': '',
        'end_date': '',
        'purpose': '',
    })




# views pages

def technical_task_list(request):
    technical_tasks = TechnicalTask.objects.select_related('oid').all()
    return render(request, 'views/technical_task_list.html', {'technical_tasks': technical_tasks})

def trip_list(request):
    query = request.GET.get("q", "")
    trips = Trip.objects.all()

    if query:
        trips = trips.filter(
            Q(purpose__icontains=query) |
            Q(units__name__icontains=query) |
            Q(oids__name__icontains=query)
        ).distinct()

    return render(request, 'views/trip_list.html', {'trips': trips})

def unit_overview(request):
    selected_unit_id = request.GET.get('unit')
    units = Unit.objects.all()
    
    if selected_unit_id:
        oids = OID.objects.filter(unit__id=selected_unit_id).order_by('name')
    else:
        oids = OID.objects.all().order_by('unit', 'name')

    return render(request, 'views/unit_overview.html', {
        'oids': oids,
        'units': units,
        'selected_unit_id': selected_unit_id
    })

def oid_details(request, oid_id):
    oid = get_object_or_404(OID, pk=oid_id)

    status_changes = OIDStatusChange.objects.filter(oid=oid).order_by('-changed_at')
    work_items = WorkRequestItem.objects.filter(oid=oid).select_related('request')
    tech_tasks = TechnicalTask.objects.filter(oid=oid)
    documents = Document.objects.filter(oid=oid).distinct()

    return render(request, 'views/oid_details.html', {
        'oid': oid,
        'status_changes': status_changes,
        'work_items': work_items,
        'tech_tasks': tech_tasks,
        'documents': documents,
    })


from .forms import MainFilterForm

def filters_example(request):
    form = MainFilterForm(request.GET) # Важливо: ініціалізуємо форму даними з GET-запиту

    # Тут може бути логіка для фільтрації основних даних, які ви виводите на сторінку
    # на основі значень з `form.cleaned_data` (якщо форма валідна)
    # Наприклад:
    # if form.is_valid():
    #     selected_unit = form.cleaned_data.get('unit')
    #     selected_oid = form.cleaned_data.get('oid')
    #     # ... фільтруйте ваш основний QuerySet

    context = {
        'form': form,
        # 'some_filtered_data': some_filtered_data, # Додайте, якщо ви показуєте відфільтровані дані
    }
    return render(request, 'oids/filters_example.html', context)

# ... (ваш existing get_filtered_options view) ...
# ... (ваші existing AJAX views like load-oids-for-unit, load-oids-for-units, get-requests-by-oid, etc.) ...
# ... (ваш existing get-work-request-details view) ...
# ... (ваш existing load-technical-tasks-for-oid view) ...